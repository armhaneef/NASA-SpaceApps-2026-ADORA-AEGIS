import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { applyAnatomyStyle, getFocusDistance, getLayerAlertIndicators, prepareAnatomyModel } from '../src/anatomyScene.js'
import { getAnatomySelection, getLocalizedFindings, ORGAN_STRUCTURES } from '../src/anatomyRegions.js'
import { createDemoSnapshot, evaluateSyntheticAlerts } from '../src/healthAlerts.js'

const bytes = await readFile(new URL('../public/models/adora-anatomy.glb', import.meta.url))
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
const { scene } = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '')
const withModel = (fn) => {
  const model = prepareAnatomyModel(scene)
  try { return fn(model) } finally { model.clonedMaterials.forEach((material) => material.dispose()) }
}
const mesh = (model, name) => model.scene.getObjectByName(name)

test('real GLB inventory verifies all 34 organ meshes and individually mapped structures', () => withModel((model) => {
  assert.equal(model.info.meshNames.length, 128)
  assert.equal(model.info.meshesByLayer.organs.length, 34)
  for (const { mesh: name } of Object.values(ORGAN_STRUCTURES)) {
    assert.ok(model.info.meshesByLayer.organs.includes(name), name)
    assert.ok(model.info.focusPoints[getAnatomySelection(name)], name)
  }
  for (const name of ['brain', 'brainstem', 'cerebellum', 'heart', 'lung_l', 'lung_r']) assert.ok(mesh(model, name), name)
}))

test('muscles retain real head references, neck muscles, hands and all limbs', () => withModel((model) => {
  applyAnatomyStyle(model, { layer: 'muscles' })
  for (const name of ['skull', 'mandible', 'teeth', 'eye_l', 'eye_r']) {
    assert.equal(mesh(model, name).visible, true, name)
    assert.ok(mesh(model, name).material.opacity < 0.3)
  }
  for (const name of model.info.meshesByLayer.muscles) assert.equal(mesh(model, name).visible, true, name)
  assert.equal(mesh(model, 'heart').visible, false)
  assert.equal(model.info.meshesByLayer.muscles.some((name) => /face|scalp/.test(name)), false)
  assert.equal(getLayerAlertIndicators(model.info.layerCoverage, { leftEye: 'warning' }).muscles, 'warning')
}))

test('organ layer retains every actual organ and a non-pickable body reference', () => withModel((model) => {
  applyAnatomyStyle(model, { layer: 'organs' })
  for (const name of model.info.meshesByLayer.organs) {
    assert.equal(mesh(model, name).visible, true, name)
    assert.equal(mesh(model, name).userData.aegisPickable, true, name)
  }
  const skin = mesh(model, model.info.meshesByLayer.skin[0])
  assert.equal(skin.visible, true)
  assert.equal(skin.userData.aegisPickable, false)
  assert.ok(skin.material.opacity < 0.1)
  assert.equal(mesh(model, 'femur_r').visible, false)
}))

test('head and brain focus reveal verified brain without moving or resizing geometry', () => withModel((model) => {
  const brain = mesh(model, 'brain')
  const originalMatrix = brain.matrixWorld.toArray()
  for (const selected of ['head', 'brain']) {
    applyAnatomyStyle(model, { layer: 'muscles', selected })
    assert.equal(brain.visible, true)
    assert.equal(mesh(model, 'skull').visible, true)
    assert.ok(mesh(model, 'skull').material.opacity < 0.12)
    assert.deepEqual(brain.matrixWorld.toArray(), originalMatrix)
    assert.ok(model.info.focusRadii.brain >= model.info.focusRadii.head)
  }
}))

test('critical right arm persists through selection and all supported layers without organ indicators', () => withModel((model) => {
  const snapshot = createDemoSnapshot('right-arm-alert')
  const { regionStatuses } = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })
  for (const layer of ['full', 'muscles', 'skeleton', 'organs']) {
    applyAnatomyStyle(model, { layer, selected: 'rightArm', regionStatuses })
    for (const name of model.info.meshNames) {
      const object = mesh(model, name)
      if (object.userData.aegisRegion === 'rightArm') assert.equal(object.material.color.getHexString(), 'ff4757', name)
      else if (object.userData.aegisLayer !== 'skin') assert.equal(object.material.color.getHexString(), '00d5f2', name)
    }
  }
  assert.deepEqual(getLayerAlertIndicators(model.info.layerCoverage, regionStatuses), {
    full: 'critical', skeleton: 'critical', muscles: 'critical', organs: null,
  })
}))

test('individual liver marker does not color stomach or imply a skeleton finding', () => withModel((model) => {
  const marker = { region: 'liver', severity: 'critical', source: 'demo-region-simulation', reason: 'Explicit synthetic liver marker.' }
  const { regionStatuses, alerts } = evaluateSyntheticAlerts({}, { regionAlerts: [marker] })
  applyAnatomyStyle(model, { layer: 'organs', regionStatuses, selected: 'liver' })
  assert.equal(mesh(model, 'liver').material.color.getHexString(), 'ff4757')
  assert.equal(mesh(model, 'stomach').material.color.getHexString(), '00d5f2')
  assert.equal(getLayerAlertIndicators(model.info.layerCoverage, regionStatuses).organs, 'critical')
  assert.equal(getLayerAlertIndicators(model.info.layerCoverage, regionStatuses).skeleton, null)
  assert.equal(getLocalizedFindings(alerts, 'liver').length, 1)
}))

test('shared shoulder assemblies cannot spread an arm marker into the neck or torso', () => withModel((model) => {
  applyAnatomyStyle(model, { layer: 'muscles', regionStatuses: { rightArm: 'critical' } })
  for (const name of ['shoulder_muscles_l', 'shoulder_muscles_r', 'neck_muscles_r', 'chest_muscles_r']) {
    assert.equal(mesh(model, name).visible, true, name)
    assert.equal(mesh(model, name).material.color.getHexString(), '00d5f2', name)
  }
  assert.equal(mesh(model, 'shoulder_muscles_r').userData.aegisRegion, null)
  assert.equal(mesh(model, 'deltoid_r').material.color.getHexString(), 'ff4757')
}))

test('global-only anomalies never color meshes or light any anatomical layer indicator', () => withModel((model) => {
  const { regionStatuses } = evaluateSyntheticAlerts({ heart_rate_bpm: 120, spo2_percent: 80, respiration_rate_bpm: 30 })
  applyAnatomyStyle(model, { regionStatuses })
  for (const name of ['heart', 'lung_l', 'lung_r', 'humerus_r', 'femur_l']) assert.equal(mesh(model, name).material.color.getHexString(), '00d5f2')
  assert.ok(Object.values(getLayerAlertIndicators(model.info.layerCoverage, regionStatuses)).every((status) => status === null))
}))

test('left leg warning and simultaneous markers affect only explicit targets', () => withModel((model) => {
  const regionAlerts = [
    { region: 'leftLeg', severity: 'warning', source: 'demo-region-simulation', reason: 'Explicit left leg demo.' },
    { region: 'rightArm', severity: 'critical', source: 'demo-region-simulation', reason: 'Explicit right arm demo.' },
  ]
  const { regionStatuses } = evaluateSyntheticAlerts({}, { regionAlerts })
  applyAnatomyStyle(model, { layer: 'muscles', regionStatuses })
  assert.equal(mesh(model, 'quadriceps_l').material.color.getHexString(), 'ffd43b')
  assert.equal(mesh(model, 'upper_arm_muscles_r').material.color.getHexString(), 'ff4757')
  assert.equal(mesh(model, 'quadriceps_r').material.color.getHexString(), '00d5f2')
}))

test('unknown regional data is neutral grey in live mode while demo references stay cyan', () => withModel((model) => {
  applyAnatomyStyle(model, { isDemo: false })
  assert.equal(mesh(model, 'heart').material.color.getHexString(), '8499a0')
  applyAnatomyStyle(model, { isDemo: true })
  assert.equal(mesh(model, 'heart').material.color.getHexString(), '00d5f2')
}))

test('missing brain has no invented focus point and leaves a useful head reference', () => {
  const partial = scene.clone(true)
  for (const name of ['brain', 'brainstem', 'cerebellum', 'pituitary']) partial.getObjectByName(name)?.removeFromParent()
  const model = prepareAnatomyModel(partial)
  try {
    assert.equal(model.info.focusPoints.brain, undefined)
    assert.ok(model.info.focusPoints.head)
    applyAnatomyStyle(model, { layer: 'muscles', selected: 'head' })
    assert.equal(mesh(model, 'skull').visible, true)
  } finally { model.clonedMaterials.forEach((material) => material.dispose()) }
})

test('camera fitting accounts for narrow viewports and stays within orbit limits', () => {
  assert.ok(getFocusDistance(0.4, 0.5) > getFocusDistance(0.4, 1.5))
  assert.ok(getFocusDistance(0.01, 1) >= 1.15)
  assert.ok(getFocusDistance(10, 0.5) <= 5.8)
})
