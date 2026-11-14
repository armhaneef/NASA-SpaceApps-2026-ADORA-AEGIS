import assert from 'node:assert/strict'
import test from 'node:test'
import {
  createDemoSnapshot,
  DEMO_SCENARIOS,
  DEMO_THRESHOLDS,
  evaluateSyntheticAlerts,
  HEALTH_SEVERITY_COLORS,
  HEALTH_BASELINE,
} from '../src/healthAlerts.js'
import { getAnatomyRegion } from '../src/anatomyRegions.js'

test('all six demo scenarios create complete, synthetic readings', () => {
  assert.equal(DEMO_SCENARIOS.length, 6)

  for (const scenario of DEMO_SCENARIOS) {
    const snapshot = createDemoSnapshot(scenario.id)
    assert.deepEqual(Object.keys(snapshot.readings).sort(), Object.keys(HEALTH_BASELINE).sort())
    assert.equal(snapshot.scenarioId, scenario.id)
  }
})

test('health severity colors use the specified holographic palette', () => {
  assert.deepEqual(HEALTH_SEVERITY_COLORS, {
    normal: '#00D9FF',
    warning: '#FFCC00',
    critical: '#FF304F',
  })
})

test('verified side-specific arm meshes map to their full arm regions', () => {
  for (const mesh of ['shoulder_muscles_r', 'upper_arm_muscles_r', 'forearm_muscles_r', 'forearm_r', 'hand_muscles_r', 'hand_r', 'clavicle_r']) {
    assert.equal(getAnatomyRegion(mesh), 'rightArm', mesh)
  }
  for (const mesh of ['shoulder_muscles_l', 'upper_arm_muscles_l', 'forearm_muscles_l', 'forearm_l', 'hand_muscles_l', 'hand_l', 'clavicle_l']) {
    assert.equal(getAnatomyRegion(mesh), 'leftArm', mesh)
  }
})

test('head and brain meshes remain independently selectable and unknown meshes stay unmapped', () => {
  assert.equal(getAnatomyRegion('skull'), 'head')
  assert.equal(getAnatomyRegion('brain'), 'brain')
  assert.equal(getAnatomyRegion('brainstem'), 'brain')
  assert.equal(getAnatomyRegion('unknown_mesh_r'), null)
  assert.equal(getAnatomyRegion(null), null)
})

test('normal scenario has no alerts and localized alert states clear', () => {
  const snapshot = createDemoSnapshot('normal')
  const result = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })

  assert.deepEqual(result.alerts, [])
  assert.equal(result.regionStatuses.heart, 'normal')
  assert.equal(result.regionStatuses.leftArm, 'no-data')
})

test('heart thresholds recognize configured high and low deviations', () => {
  assert.equal(evaluateSyntheticAlerts({ heart_rate_bpm: 92 }).regionStatuses.heart, 'warning')
  assert.equal(evaluateSyntheticAlerts({ heart_rate_bpm: 107 }).regionStatuses.heart, 'critical')
  assert.equal(evaluateSyntheticAlerts({ heart_rate_bpm: 57 }).regionStatuses.heart, 'warning')
  assert.equal(evaluateSyntheticAlerts({ heart_rate_bpm: 47 }).regionStatuses.heart, 'critical')
})

test('respiratory readings highlight both lungs and not unrelated regions', () => {
  const snapshot = createDemoSnapshot('respiratory-alert')
  const result = evaluateSyntheticAlerts(snapshot.readings)

  assert.equal(result.regionStatuses.leftLung, 'critical')
  assert.equal(result.regionStatuses.rightLung, 'critical')
  assert.equal(result.regionStatuses.heart, 'normal')
  assert.equal(result.regionStatuses.leftArm, 'no-data')
  assert.equal(result.regionStatuses.abdomen, 'no-data')
  assert.equal(result.alerts.length, 4)
})

test('the most severe concurrent respiratory result controls the region color', () => {
  const result = evaluateSyntheticAlerts({
    spo2_percent: 89,
    respiration_rate_bpm: 22,
  })

  assert.equal(result.regionStatuses.leftLung, 'critical')
  assert.equal(result.regionStatuses.rightLung, 'critical')
})

test('explicit arm scenarios highlight only their named arm', () => {
  const left = createDemoSnapshot('left-arm-alert')
  const leftResult = evaluateSyntheticAlerts(left.readings, { regionAlerts: left.regionAlerts })
  assert.equal(leftResult.regionStatuses.leftArm, 'warning')
  assert.equal(leftResult.regionStatuses.rightArm, 'no-data')

  const right = createDemoSnapshot('right-arm-alert')
  const rightResult = evaluateSyntheticAlerts(right.readings, { regionAlerts: right.regionAlerts })
  assert.equal(rightResult.regionStatuses.rightArm, 'critical')
  assert.equal(rightResult.regionStatuses.leftArm, 'no-data')
})

test('multiple scenario combines vital and explicit regional alerts', () => {
  const snapshot = createDemoSnapshot('multiple-alerts')
  const result = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })

  assert.equal(result.regionStatuses.heart, 'critical')
  assert.equal(result.regionStatuses.leftLung, 'warning')
  assert.equal(result.regionStatuses.rightLung, 'warning')
  assert.equal(result.regionStatuses.leftArm, 'warning')
  assert.equal(result.regionStatuses.rightArm, 'critical')
  assert.equal(result.regionStatuses.rightLeg, 'warning')
  assert.equal(result.alerts.length, 8)
})

test('multiple severity sources preserve the highest region severity', () => {
  const result = evaluateSyntheticAlerts(
    { heart_rate_bpm: 110 },
    {
      regionAlerts: [
        {
          region: 'heart',
          severity: 'warning',
          source: 'demo-region-simulation',
          reason: 'Lower-priority localized demo marker.',
        },
      ],
    },
  )

  assert.equal(result.regionStatuses.heart, 'critical')
})

test('missing and non-finite readings do not produce alerts', () => {
  const result = evaluateSyntheticAlerts({
    heart_rate_bpm: Number.NaN,
    spo2_percent: undefined,
    respiration_rate_bpm: Infinity,
  })

  assert.deepEqual(result.alerts, [])
  assert.equal(result.regionStatuses.heart, 'no-data')
  assert.equal(result.regionStatuses.leftLung, 'no-data')
})

test('threshold overrides are supported and malformed thresholds are rejected', () => {
  const thresholds = {
    ...DEMO_THRESHOLDS,
    heart_rate_bpm: {
      ...DEMO_THRESHOLDS.heart_rate_bpm,
      high: { warning: 10, critical: 20 },
    },
  }
  assert.equal(evaluateSyntheticAlerts({ heart_rate_bpm: 83 }, { thresholds }).regionStatuses.heart, 'warning')
  assert.throws(
    () => evaluateSyntheticAlerts({ heart_rate_bpm: 110 }, {
      thresholds: {
        ...thresholds,
        heart_rate_bpm: { high: { warning: 25, critical: 20 } },
      },
    }),
    TypeError,
  )
})

test('unknown scenarios throw and invalid localized markers are ignored', () => {
  assert.throws(() => createDemoSnapshot('not-a-scenario'), RangeError)
  const result = evaluateSyntheticAlerts(HEALTH_BASELINE, {
    regionAlerts: [
      { region: 'leftArm', severity: 'critical', source: 'demo-region-simulation', reason: 'valid marker' },
      { region: 'leftLeg', severity: 'critical', source: 'derived-from-heart-rate', reason: 'invalid source' },
    ],
  })
  assert.equal(result.alerts.length, 1)
  assert.equal(result.regionStatuses.leftArm, 'critical')
  assert.equal(result.regionStatuses.leftLeg, 'no-data')
})
