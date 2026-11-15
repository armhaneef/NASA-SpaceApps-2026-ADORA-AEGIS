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

test('all demo scenarios create complete, synthetic readings', () => {
  assert.equal(DEMO_SCENARIOS.length, 10)

  for (const scenario of DEMO_SCENARIOS) {
    const snapshot = createDemoSnapshot(scenario.id)
    assert.deepEqual(Object.keys(snapshot.readings).sort(), Object.keys(HEALTH_BASELINE).sort())
    assert.equal(snapshot.scenarioId, scenario.id)
  }
})

test('health severity colors use the specified holographic palette', () => {
  assert.deepEqual(HEALTH_SEVERITY_COLORS, {
    normal: '#00D5F2',
    warning: '#FFD43B',
    critical: '#FF4757',
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

test('actual side-specific GLB leg meshes map to their matching leg regions', () => {
  for (const mesh of ['foot_muscles_l', 'foot_l', 'calf_l', 'shin_muscles_l', 'femur_l', 'lower_leg_l', 'patella_l', 'veins_leg_l', 'arteries_leg_l', 'adductors_l', 'hamstrings_l', 'quadriceps_l', 'gluteal_l', 'iliopsoas_l']) {
    assert.equal(getAnatomyRegion(mesh), 'leftLeg', mesh)
  }
  for (const mesh of ['foot_muscles_r', 'foot_r', 'calf_r', 'shin_muscles_r', 'femur_r', 'lower_leg_r', 'patella_r', 'veins_leg_r', 'arteries_leg_r', 'adductors_r', 'hamstrings_r', 'quadriceps_r', 'gluteal_r', 'iliopsoas_r']) {
    assert.equal(getAnatomyRegion(mesh), 'rightLeg', mesh)
  }
})

test('head and brain meshes remain independently selectable and unknown meshes stay unmapped', () => {
  assert.equal(getAnatomyRegion('skull'), 'head')
  assert.equal(getAnatomyRegion('brain'), 'brain')
  assert.equal(getAnatomyRegion('brainstem'), 'brain')
  assert.equal(getAnatomyRegion('unknown_mesh_r'), null)
  assert.equal(getAnatomyRegion(null), null)
})

test('normal scenario has no alerts and has no unsupported region states', () => {
  const snapshot = createDemoSnapshot('normal')
  const result = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })

  assert.deepEqual(result.alerts, [])
  assert.equal(result.regionStatuses.heart, 'no-data')
  assert.equal(result.regionStatuses.leftLung, 'no-data')
  assert.equal(result.regionStatuses.rightLung, 'no-data')
  assert.equal(result.regionStatuses.leftArm, 'no-data')
  assert.equal(result.regionStatuses.rightArm, 'no-data')
  assert.equal(result.regionStatuses.leftLeg, 'no-data')
  assert.equal(result.regionStatuses.rightLeg, 'no-data')
})

test('heart-rate thresholds remain global and never localize to the heart', () => {
  const cases = [
    [92, 'warning'],
    [107, 'critical'],
    [57, 'warning'],
    [47, 'critical'],
  ]

  for (const [heartRate, severity] of cases) {
    const result = evaluateSyntheticAlerts({ heart_rate_bpm: heartRate })
    assert.equal(result.alerts.length, 1)
    assert.equal(result.alerts[0].measurementKey, 'heart_rate_bpm')
    assert.equal(result.alerts[0].scope, 'global')
    assert.equal(result.alerts[0].region, null)
    assert.equal(result.alerts[0].severity, severity)
    assert.equal(result.regionStatuses.heart, 'no-data')
  }
})

test('SpO2 and respiration alerts remain global and do not highlight either lung', () => {
  const snapshot = createDemoSnapshot('respiratory-alert')
  const result = evaluateSyntheticAlerts(snapshot.readings)

  assert.deepEqual(result.alerts.map(({ measurementKey, scope, region, severity }) => ({
    measurementKey,
    scope,
    region,
    severity,
  })), [
    { measurementKey: 'spo2_percent', scope: 'global', region: null, severity: 'critical' },
    { measurementKey: 'respiration_rate_bpm', scope: 'global', region: null, severity: 'critical' },
  ])
  assert.equal(result.regionStatuses.leftLung, 'no-data')
  assert.equal(result.regionStatuses.rightLung, 'no-data')
  assert.equal(result.regionStatuses.heart, 'no-data')
  assert.equal(result.regionStatuses.leftArm, 'no-data')
  assert.equal(result.regionStatuses.rightArm, 'no-data')
  assert.equal(result.regionStatuses.leftLeg, 'no-data')
  assert.equal(result.regionStatuses.rightLeg, 'no-data')
  assert.equal(result.regionStatuses.abdomen, 'no-data')
})

test('global alert severity does not change lung region status', () => {
  const result = evaluateSyntheticAlerts({
    spo2_percent: 89,
    respiration_rate_bpm: 22,
  })

  assert.equal(result.alerts.length, 2)
  assert.equal(result.alerts[0].severity, 'critical')
  assert.equal(result.alerts[1].severity, 'warning')
  assert.equal(result.regionStatuses.leftLung, 'no-data')
  assert.equal(result.regionStatuses.rightLung, 'no-data')
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
  assert.equal(leftResult.alerts[0].source, 'demo-region-simulation')
  assert.equal(rightResult.alerts[0].source, 'demo-region-simulation')
})

test('critical limb scenarios map only the named limb and carry synthetic provenance', () => {
  const cases = [
    ['left-arm-critical', 'leftArm', 'demo-left-arm-critical'],
    ['right-arm-alert', 'rightArm', 'demo-right-arm-critical'],
    ['left-leg-critical', 'leftLeg', 'demo-left-leg-critical'],
    ['right-leg-critical', 'rightLeg', 'demo-right-leg-critical'],
  ]
  const limbRegions = ['leftArm', 'rightArm', 'leftLeg', 'rightLeg']

  for (const [scenarioId, expectedRegion, expectedId] of cases) {
    const snapshot = createDemoSnapshot(scenarioId)
    const result = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })
    const [alert] = result.alerts

    assert.equal(result.alerts.length, 1, scenarioId)
    assert.equal(alert.id, expectedId)
    assert.equal(alert.region, expectedRegion)
    assert.equal(alert.scope, 'localized')
    assert.equal(alert.severity, 'critical')
    assert.equal(alert.source, 'demo-region-simulation')
    assert.match(alert.reason, /synthetic localized critical marker/i)
    assert.match(alert.reason, /not a medical diagnosis/i)
    assert.equal(HEALTH_SEVERITY_COLORS[alert.severity], '#FF4757')
    for (const region of limbRegions) {
      assert.equal(result.regionStatuses[region], region === expectedRegion ? 'critical' : 'no-data', `${scenarioId}: ${region}`)
    }
  }
})

test('multiple localized critical markers highlight only the left arm and right leg', () => {
  const snapshot = createDemoSnapshot('multiple-localized-critical')
  const result = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })
  const identifiers = result.alerts.map((alert) => alert.id)

  assert.equal(result.alerts.length, 2)
  assert.equal(new Set(identifiers).size, identifiers.length)
  assert.deepEqual(result.alerts.map(({ region, severity, scope, source }) => ({ region, severity, scope, source })), [
    { region: 'leftArm', severity: 'critical', scope: 'localized', source: 'demo-region-simulation' },
    { region: 'rightLeg', severity: 'critical', scope: 'localized', source: 'demo-region-simulation' },
  ])
  assert.equal(result.regionStatuses.leftArm, 'critical')
  assert.equal(result.regionStatuses.rightLeg, 'critical')
  assert.equal(result.regionStatuses.rightArm, 'no-data')
  assert.equal(result.regionStatuses.leftLeg, 'no-data')
})

test('switching from a localized critical scenario to normal clears limb highlights', () => {
  const critical = createDemoSnapshot('right-leg-critical')
  const criticalResult = evaluateSyntheticAlerts(critical.readings, { regionAlerts: critical.regionAlerts })
  const normal = createDemoSnapshot('normal')
  const normalResult = evaluateSyntheticAlerts(normal.readings, { regionAlerts: normal.regionAlerts })

  assert.equal(criticalResult.regionStatuses.rightLeg, 'critical')
  assert.deepEqual(normalResult.alerts, [])
  assert.deepEqual(
    ['leftArm', 'rightArm', 'leftLeg', 'rightLeg'].map((region) => normalResult.regionStatuses[region]),
    ['no-data', 'no-data', 'no-data', 'no-data'],
  )
})

test('multiple scenario keeps vital alerts global and highlights only explicit regions', () => {
  const snapshot = createDemoSnapshot('multiple-alerts')
  const result = evaluateSyntheticAlerts(snapshot.readings, { regionAlerts: snapshot.regionAlerts })

  assert.equal(result.regionStatuses.heart, 'no-data')
  assert.equal(result.regionStatuses.leftLung, 'no-data')
  assert.equal(result.regionStatuses.rightLung, 'no-data')
  assert.equal(result.regionStatuses.leftArm, 'warning')
  assert.equal(result.regionStatuses.rightArm, 'critical')
  assert.equal(result.regionStatuses.rightLeg, 'warning')
  assert.equal(result.alerts.length, 6)
  assert.equal(result.alerts.filter((alert) => alert.scope === 'global').length, 3)
  assert.equal(result.alerts.filter((alert) => alert.source === 'demo-region-simulation').length, 3)
})

test('a global heart-rate alert does not override an explicit regional marker', () => {
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

  assert.equal(result.alerts.find((alert) => alert.scope === 'global').severity, 'critical')
  assert.equal(result.regionStatuses.heart, 'warning')
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
  const result = evaluateSyntheticAlerts({ heart_rate_bpm: 83 }, { thresholds })
  assert.equal(result.alerts[0].severity, 'warning')
  assert.equal(result.alerts[0].region, null)
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
