import { useEffect, useMemo, useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { getAnatomyRegion } from './anatomyRegions.js'
import { HEALTH_SEVERITY_COLORS } from './healthAlerts.js'

const MODEL_PATH = '/models/adora-anatomy.glb'
const TARGET_HEIGHT = 3.1

async function loadModel(signal) {
  const response = await fetch(MODEL_PATH, { signal })
  if (!response.ok) {
    const error = new Error(`Model request returned ${response.status}`)
    error.status = response.status
    throw error
  }

  if (response.headers.get('content-type')?.includes('text/html')) {
    const error = new Error('Model path returned HTML instead of a GLB file')
    error.status = 404
    throw error
  }

  const loader = new GLTFLoader()
  loader.setMeshoptDecoder(MeshoptDecoder)

  const arrayBuffer = await response.arrayBuffer()
  return new Promise((resolve, reject) => {
    loader.parse(
      arrayBuffer,
      `${window.location.origin}/`,
      resolve,
      reject,
    )
  })
}

function getCloneModel(scene) {
  const clone = scene.clone(true)
  const clonedMaterials = []
  const regionBounds = new Map()

  clone.traverse((object) => {
    if (!object.isMesh) return

    object.userData.aegisRegion = getAnatomyRegion(object.name)
    object.material = Array.isArray(object.material)
      ? object.material.map((material) => {
        const copy = material.clone()
        copy.userData.aegisOriginal = {
          color: copy.color.clone(),
          emissive: copy.emissive.clone(),
          emissiveIntensity: copy.emissiveIntensity,
          roughness: copy.roughness,
          metalness: copy.metalness,
          transparent: copy.transparent,
          opacity: copy.opacity,
          depthWrite: copy.depthWrite,
          side: copy.side,
          wireframe: copy.wireframe,
        }
        clonedMaterials.push(copy)
        return copy
      })
      : (() => {
        const copy = object.material.clone()
        copy.userData.aegisOriginal = {
          color: copy.color.clone(),
          emissive: copy.emissive.clone(),
          emissiveIntensity: copy.emissiveIntensity,
          roughness: copy.roughness,
          metalness: copy.metalness,
          transparent: copy.transparent,
          opacity: copy.opacity,
          depthWrite: copy.depthWrite,
          side: copy.side,
          wireframe: copy.wireframe,
        }
        clonedMaterials.push(copy)
        return copy
      })()
    object.frustumCulled = true
  })

  const bounds = new THREE.Box3().setFromObject(clone)
  const size = bounds.getSize(new THREE.Vector3())
  const center = bounds.getCenter(new THREE.Vector3())
  const scale = TARGET_HEIGHT / Math.max(size.y, 0.001)
  clone.position.sub(center)
  clone.updateMatrixWorld(true)

  clone.traverse((object) => {
    const region = object.userData.aegisRegion
    if (!object.isMesh || !region) return

    const meshBounds = new THREE.Box3().setFromObject(object)
    if (!meshBounds.isEmpty()) {
      const current = regionBounds.get(region) ?? new THREE.Box3()
      current.union(meshBounds)
      regionBounds.set(region, current)
    }
  })

  const focusPoints = {}
  const localPositions = {}
  for (const [region, regionBoundsForName] of regionBounds) {
    const point = regionBoundsForName.getCenter(new THREE.Vector3())
    localPositions[region] = point.toArray()
    focusPoints[region] = point.multiplyScalar(scale).toArray()
  }

  return { scene: clone, scale, clonedMaterials, focusPoints, localPositions }
}

function getLayerGroup(object) {
  let current = object
  while (current) {
    const name = current.name?.toLowerCase()
    if (['skin', 'skeleton', 'muscles', 'organs', 'vessels', 'nerves'].includes(name)) {
      return name
    }
    current = current.parent
  }
  return null
}

function styleModel(model, mode, selected, regionStatuses, layer = 'full') {
  const criticalMaterials = []

  model.scene.traverse((object) => {
    if (!object.isMesh) return

    const region = object.userData.aegisRegion
    const layerGroup = getLayerGroup(object)
    const isSkin = object.name.toLowerCase() === 'skin'
    const materials = Array.isArray(object.material) ? object.material : [object.material]
    const isSelected = region && selected === region
    const isWireframe = mode === 'wireframe'
    const status = regionStatuses[region] ?? 'normal'
    const severityColor = HEALTH_SEVERITY_COLORS[status] ?? HEALTH_SEVERITY_COLORS.normal
    const layerMatch = layer === 'full' || layerGroup === layer
    const keepVisible = isSelected || layerMatch
    object.visible = keepVisible

    materials.forEach((material) => {
      const original = material.userData.aegisOriginal
      const paletteColor = isSkin ? '#4f9bac' : severityColor

      material.color.copy(original.color)
      material.emissive.copy(original.emissive)
      material.emissiveIntensity = original.emissiveIntensity
      material.roughness = 0.48
      material.metalness = 0.12
      material.transparent = true
      material.color.set(paletteColor)
      material.emissive.set(paletteColor)
      material.emissiveIntensity = isSkin ? 0.12 : isSelected ? 0.58 : status === 'critical' ? 0.38 : 0.24

      const layerOpacity = layer === 'full'
        ? (isSkin ? 0.19 : 0.76)
        : layerGroup === 'skin'
          ? 0.04
          : layerGroup === 'skeleton'
            ? 0.96
            : layerGroup === 'muscles'
              ? 0.92
              : layerGroup === 'organs'
                ? 0.92
                : layerGroup === 'vessels'
                  ? 0.86
                  : layerGroup === 'nerves'
                    ? 0.8
                    : 0.7

      material.opacity = isSkin
        ? mode === 'outer' ? layerOpacity : 0.055
        : isWireframe
          ? 0.9
          : isSelected
            ? 0.96
            : layer === 'full' || layerGroup === layer
              ? layerOpacity
              : layerGroup === null
                ? 0.7
                : 0.18

      material.depthWrite = false
      material.side = THREE.DoubleSide
      material.wireframe = isWireframe
      material.needsUpdate = true
      if (status === 'critical') {
        material.userData.aegisAlertIntensity = isSelected ? 0.68 : 0.48
        criticalMaterials.push(material)
      }
    })
  })

  return criticalMaterials
}

function FallbackSilhouette() {
  return (
    <group>
      <mesh position={[0, 0.1, 0]}>
        <capsuleGeometry args={[0.42, 1.6, 8, 24]} />
        <meshBasicMaterial
          color="#58cfe9"
          transparent
          opacity={0.12}
          wireframe
          depthWrite={false}
        />
      </mesh>
      <mesh position={[0, 1.15, 0]}>
        <sphereGeometry args={[0.25, 24, 16]} />
        <meshBasicMaterial
          color="#58cfe9"
          transparent
          opacity={0.16}
          wireframe
          depthWrite={false}
        />
      </mesh>
    </group>
  )
}

function LoadedModel({ scene, mode, layer, selected, regionStatuses, onSelect, onModelInfo, reducedMotion }) {
  const model = useMemo(() => getCloneModel(scene), [scene])
  const criticalMaterials = useRef([])

  useEffect(() => {
    criticalMaterials.current = styleModel(model, mode, selected, regionStatuses, layer)
  }, [model, mode, regionStatuses, selected, layer])

  useFrame(({ clock }) => {
    if (reducedMotion) return
    const pulse = 0.82 + Math.sin(clock.elapsedTime * 5) * 0.18
    criticalMaterials.current.forEach((material) => {
      material.emissiveIntensity = material.userData.aegisAlertIntensity * pulse
    })
  })

  useEffect(() => {
    onModelInfo({ focusPoints: model.focusPoints, localPositions: model.localPositions })
    return () => {
      model.clonedMaterials.forEach((material) => material.dispose())
    }
  }, [model, onModelInfo])

  return (
    <group scale={model.scale}>
      <primitive
        object={model.scene}
        onClick={(event) => {
          if (event.delta > 5) return
          const region = event.object.userData.aegisRegion
          if (region) {
            event.stopPropagation()
            onSelect(region)
          } else if (event.object.name.toLowerCase() === 'skin') {
            const nearestRegion = Object.entries(model.focusPoints)
              .reduce((nearest, [candidate, position]) => {
                const distance = event.point.distanceToSquared(new THREE.Vector3(...position))
                return distance < nearest.distance ? { region: candidate, distance } : nearest
              }, { region: null, distance: Infinity }).region
            if (nearestRegion) {
              event.stopPropagation()
              onSelect(nearestRegion)
            }
          }
        }}
      />
    </group>
  )
}

export default function AnatomyModel({
  mode,
  layer,
  selected,
  regionStatuses,
  onSelect,
  onStatusChange,
  onModelInfo,
  reducedMotion = false,
}) {
  const [asset, setAsset] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    loadModel(controller.signal)
      .then((gltf) => {
        if (!active) return
        setAsset(gltf.scene)
        setStatus('ready')
      })
      .catch((error) => {
        if (!active || error.name === 'AbortError') return
        const missing = error.status === 404
        setStatus(missing ? 'missing' : 'error')
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [])

  useEffect(() => {
    onStatusChange(status)
    if (status !== 'ready') onModelInfo({})
  }, [onModelInfo, onStatusChange, status])

  return (
    <group>
      {asset ? (
        <LoadedModel
          scene={asset}
          mode={mode}
          layer={layer}
          selected={selected}
          regionStatuses={regionStatuses}
          onSelect={onSelect}
          onModelInfo={onModelInfo}
          reducedMotion={reducedMotion}
        />
      ) : (
        <FallbackSilhouette />
      )}
    </group>
  )
}
