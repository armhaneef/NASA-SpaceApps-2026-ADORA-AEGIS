import * as THREE from 'three'
import { getAnatomyRegion, getAnatomySelection, getSelectionStatus } from './anatomyRegions.js'
import { HEALTH_SEVERITY_COLORS } from './healthAlerts.js'

const LAYERS = ['skin', 'skeleton', 'muscles', 'organs', 'vessels', 'nerves']
const HEAD_REFERENCE = new Set(['skull', 'mandible', 'teeth', 'eye_l', 'eye_r'])
const BRAIN = new Set(['brain', 'brainstem', 'cerebellum'])

function layerOf(object) {
  for (let parent = object; parent; parent = parent.parent) {
    if (LAYERS.includes(parent.name.toLowerCase())) return parent.name.toLowerCase()
  }
  return null
}

export function prepareAnatomyModel(scene) {
  const clone = scene.clone(true)
  const clonedMaterials = []
  const boundsBySelection = new Map()
  const coverage = Object.fromEntries(['full', 'skeleton', 'muscles', 'organs'].map((layer) => [layer, new Set()]))
  const meshNames = []
  const meshesByLayer = Object.fromEntries(LAYERS.map((layer) => [layer, []]))
  const bounds = new THREE.Box3().setFromObject(clone)
  const scale = 3.1 / Math.max(bounds.getSize(new THREE.Vector3()).y, 0.001)
  clone.position.sub(bounds.getCenter(new THREE.Vector3()))
  clone.updateMatrixWorld(true)

  clone.traverse((object) => {
    if (!object.isMesh) return
    const selection = getAnatomySelection(object.name)
    const region = getAnatomyRegion(object.name) ?? selection
    const layer = layerOf(object)
    object.userData.aegisRegion = region
    object.userData.aegisSelection = selection
    object.userData.aegisLayer = layer
    meshNames.push(object.name)
    meshesByLayer[layer]?.push(object.name)
    const originals = Array.isArray(object.material) ? object.material : [object.material]
    const copies = originals.map((material) => {
      const copy = material.clone()
      clonedMaterials.push(copy)
      return copy
    })
    object.material = Array.isArray(object.material) ? copies : copies[0]
    const originalRaycast = object.raycast
    object.raycast = function (...args) {
      if (this.visible && this.userData.aegisPickable) originalRaycast.apply(this, args)
    }
    for (const key of new Set([region, selection].filter(Boolean))) {
      const box = new THREE.Box3().setFromObject(object)
      if (box.isEmpty()) continue
      const current = boundsBySelection.get(key) ?? new THREE.Box3()
      boundsBySelection.set(key, current.union(box))
      coverage.full.add(key)
      coverage[layer]?.add(key)
      if (HEAD_REFERENCE.has(object.name)) coverage.muscles.add(key)
    }
  })

  const focusPoints = {}, localPositions = {}, focusRadii = {}
  for (const [selection, box] of boundsBySelection) {
    const center = box.getCenter(new THREE.Vector3())
    localPositions[selection] = center.toArray()
    focusPoints[selection] = center.multiplyScalar(scale).toArray()
    focusRadii[selection] = box.getSize(new THREE.Vector3()).length() * scale / 2
  }
  // Frame the head when revealing the brain; never resize or move an organ.
  if (focusRadii.brain && focusRadii.head) focusRadii.brain = Math.max(focusRadii.brain, focusRadii.head)
  return {
    scene: clone, scale, clonedMaterials,
    info: { focusPoints, localPositions, focusRadii, meshNames, meshesByLayer,
      layerCoverage: Object.fromEntries(Object.entries(coverage).map(([layer, keys]) => [layer, [...keys]])) },
  }
}

export function applyAnatomyStyle(model, { mode = 'outer', layer = 'full', selected = null, regionStatuses = {}, isDemo = true } = {}) {
  const criticalMaterials = []
  const headFocus = selected === 'head' || selected === 'brain'
  model.scene.traverse((object) => {
    if (!object.isMesh) return
    const { aegisRegion: region, aegisSelection: selection, aegisLayer: group } = object.userData
    const isSkin = group === 'skin'
    const isHeadReference = HEAD_REFERENCE.has(object.name)
    const isBrain = BRAIN.has(object.name)
    const matchesSelection = selected && (selection === selected || region === selected)
    const isPrimary = layer === 'full' || group === layer
    const headReference = isHeadReference && (layer === 'muscles' || layer === 'organs' || headFocus)
    const brainReveal = isBrain && headFocus
    object.visible = isSkin || isPrimary || headReference || brainReveal
    object.userData.aegisContextOnly = isSkin || (!isPrimary && headReference && !headFocus)
    object.userData.aegisPickable = Boolean(selection) && !isSkin
      && (isPrimary || brainReveal || (headReference && layer === 'muscles'))
    const status = getSelectionStatus(regionStatuses, selection ?? region)
    // Cyan in demo mode is explicitly an unmarked visual reference, not a
    // normal regional measurement. Live/unknown data uses neutral grey.
    const visualStatus = isDemo && status === 'no-data' ? 'normal' : status
    object.userData.aegisVisualStatus = visualStatus
    const color = HEALTH_SEVERITY_COLORS[visualStatus]
    let opacity = layer === 'full' ? 0.72 : 0.88
    if (layer === 'organs') opacity = 0.76
    if (selected && !matchesSelection && !isSkin) opacity *= layer === 'organs' ? 0.3 : 0.65
    if (headReference && !isPrimary) opacity = 0.16
    if (matchesSelection) opacity = 0.94
    if (headFocus && isHeadReference) opacity = 0.09
    if (brainReveal) opacity = 0.92
    if (isSkin) opacity = layer === 'full' && mode === 'outer' ? 0.075 : 0.025
    const materials = Array.isArray(object.material) ? object.material : [object.material]
    for (const material of materials) {
      material.color.set(isSkin ? (isDemo ? '#4f9bac' : HEALTH_SEVERITY_COLORS['no-data']) : color)
      material.emissive.copy(material.color)
      material.emissiveIntensity = isSkin ? 0.08 : matchesSelection ? 0.38 : status === 'critical' ? 0.32 : 0.18
      material.roughness = 0.6
      material.metalness = 0.08
      material.transparent = true
      material.opacity = opacity
      material.depthWrite = false
      material.side = THREE.DoubleSide
      material.wireframe = mode === 'wireframe' && !isSkin
      if (status === 'critical' && !isSkin && object.visible) {
        material.userData.aegisAlertIntensity = material.emissiveIntensity
        criticalMaterials.push(material)
      }
    }
    object.renderOrder = isSkin ? 4 : matchesSelection || brainReveal ? 3 : 1
  })
  return criticalMaterials
}

export function getLayerAlertIndicators(layerCoverage = {}, regionStatuses = {}) {
  return Object.fromEntries(['full', 'skeleton', 'muscles', 'organs'].map((layer) => {
    const states = (layerCoverage[layer] ?? []).map((selection) => getSelectionStatus(regionStatuses, selection))
    return [layer, states.includes('critical') ? 'critical' : states.includes('warning') ? 'warning' : null]
  }))
}

export function getFocusDistance(radius, aspect, fov = 40) {
  const vertical = THREE.MathUtils.degToRad(fov / 2)
  const horizontal = Math.atan(Math.tan(vertical) * aspect)
  return THREE.MathUtils.clamp((radius || 0.25) / Math.sin(Math.min(vertical, horizontal)) * 1.18, 1.15, 5.8)
}
