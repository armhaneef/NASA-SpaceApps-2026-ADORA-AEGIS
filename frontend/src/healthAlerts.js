export const HEALTH_BASELINE = Object.freeze({
  heart_rate_bpm: 72,
  spo2_percent: 98,
  body_temperature_c: 36.7,
  respiration_rate_bpm: 16,
})

export const HEALTH_SEVERITY_COLORS = Object.freeze({
  normal: '#00D9FF',
  warning: '#FFCC00',
  critical: '#FF304F',
})

export const DEMO_THRESHOLDS = Object.freeze({
  heart_rate_bpm: Object.freeze({
    low: Object.freeze({ warning: 15, critical: 25 }),
    high: Object.freeze({ warning: 20, critical: 35 }),
  }),
  spo2_percent: Object.freeze({
    low: Object.freeze({ warning: 3, critical: 8 }),
  }),
  respiration_rate_bpm: Object.freeze({
    low: Object.freeze({ warning: 5, critical: 9 }),
    high: Object.freeze({ warning: 6, critical: 12 }),
  }),
})

const localizedAlert = (region, severity, reason) => ({
  region,
  severity,
  source: 'demo-region-simulation',
  reason,
})

export const DEMO_SCENARIOS = Object.freeze([
  { id: 'normal', label: 'Normal', readings: {} },
  { id: 'heart-alert', label: 'Heart alert', readings: { heart_rate_bpm: 110 } },
  {
    id: 'respiratory-alert',
    label: 'Respiratory alert',
    readings: { spo2_percent: 89, respiration_rate_bpm: 28 },
  },
  {
    id: 'left-arm-alert',
    label: 'Left arm alert',
    readings: {},
    regionAlerts: [
      localizedAlert('leftArm', 'warning', 'Explicit left-arm demo marker for region-visualization testing.'),
    ],
  },
  {
    id: 'right-arm-alert',
    label: 'Right arm alert',
    readings: {},
    regionAlerts: [
      localizedAlert('rightArm', 'critical', 'Explicit right-arm demo marker for region-visualization testing.'),
    ],
  },
  {
    id: 'multiple-alerts',
    label: 'Multiple alerts',
    readings: {
      heart_rate_bpm: 110,
      spo2_percent: 94,
      respiration_rate_bpm: 24,
    },
    regionAlerts: [
      localizedAlert('leftArm', 'warning', 'Explicit left-arm demo marker for multi-region visualization testing.'),
      localizedAlert('rightArm', 'critical', 'Explicit right-arm demo marker for multi-region visualization testing.'),
      localizedAlert('rightLeg', 'warning', 'Explicit right-leg demo marker for multi-region visualization testing.'),
    ],
  },
])

const REGION_KEYS = [
  'head',
  'brain',
  'heart',
  'leftLung',
  'rightLung',
  'abdomen',
  'leftArm',
  'rightArm',
  'leftLeg',
  'rightLeg',
]

const MEASUREMENT_RULES = [
  {
    key: 'heart_rate_bpm',
    label: 'Heart rate',
    unit: 'bpm',
    regions: ['heart'],
  },
  {
    key: 'spo2_percent',
    label: 'SpO₂',
    unit: '%',
    regions: ['leftLung', 'rightLung'],
  },
  {
    key: 'respiration_rate_bpm',
    label: 'Respiration rate',
    unit: '/min',
    regions: ['leftLung', 'rightLung'],
  },
]

function validateThresholds(thresholds) {
  for (const rule of MEASUREMENT_RULES) {
    const directions = thresholds?.[rule.key]
    if (!directions || typeof directions !== 'object') {
      throw new TypeError(`Missing demo thresholds for ${rule.key}`)
    }

    for (const direction of ['low', 'high']) {
      const pair = directions[direction]
      if (pair === undefined) continue
      if (
        !Number.isFinite(pair.warning)
        || !Number.isFinite(pair.critical)
        || pair.warning <= 0
        || pair.critical < pair.warning
      ) {
        throw new TypeError(`Invalid ${direction} demo thresholds for ${rule.key}`)
      }
    }
  }
}

function getSeverity(value, baseline, thresholds) {
  if (!Number.isFinite(value)) return null

  const difference = value - baseline
  const direction = difference < 0 ? 'low' : 'high'
  const limits = thresholds[direction]
  if (!limits) return null

  const deviation = Math.abs(difference)
  if (deviation >= limits.critical) return 'critical'
  if (deviation >= limits.warning) return 'warning'
  return null
}

function getValidatedRegionAlerts(regionAlerts) {
  if (!Array.isArray(regionAlerts)) return []

  return regionAlerts.filter((alert) => (
    alert
    && REGION_KEYS.includes(alert.region)
    && ['warning', 'critical'].includes(alert.severity)
    && alert.source === 'demo-region-simulation'
    && typeof alert.reason === 'string'
    && alert.reason.trim().length > 0
  ))
}

function updateRegionStatus(regionStatuses, region, severity) {
  const priority = { 'no-data': 0, normal: 1, warning: 2, critical: 3 }
  if (priority[severity] > priority[regionStatuses[region]]) {
    regionStatuses[region] = severity
  }
}

export function createDemoSnapshot(scenarioId) {
  const scenario = DEMO_SCENARIOS.find((item) => item.id === scenarioId)
  if (!scenario) throw new RangeError(`Unknown demo scenario: ${scenarioId}`)

  return {
    scenarioId: scenario.id,
    readings: { ...HEALTH_BASELINE, ...scenario.readings },
    regionAlerts: scenario.regionAlerts ?? [],
  }
}

export function evaluateSyntheticAlerts(
  readings,
  { thresholds = DEMO_THRESHOLDS, regionAlerts = [] } = {},
) {
  validateThresholds(thresholds)
  const sourceReadings = readings && typeof readings === 'object' ? readings : {}
  const regionStatuses = Object.fromEntries(REGION_KEYS.map((region) => [region, 'no-data']))
  const alerts = []

  if (Number.isFinite(sourceReadings.heart_rate_bpm)) regionStatuses.heart = 'normal'
  if (
    Number.isFinite(sourceReadings.spo2_percent)
    || Number.isFinite(sourceReadings.respiration_rate_bpm)
  ) {
    regionStatuses.leftLung = 'normal'
    regionStatuses.rightLung = 'normal'
  }

  for (const rule of MEASUREMENT_RULES) {
    const value = sourceReadings[rule.key]
    const baseline = HEALTH_BASELINE[rule.key]
    const severity = getSeverity(value, baseline, thresholds[rule.key])
    if (!severity) continue

    const difference = value - baseline
    for (const region of rule.regions) {
      alerts.push({
        id: `${rule.key}-${region}`,
        region,
        severity,
        source: 'demo-threshold',
        measurement: rule.label,
        value,
        unit: rule.unit,
        baseline,
        deviation: difference,
        reason: `${rule.label} is outside the configured synthetic demo range for this region.`,
        explanation: 'This threshold comparison is a visualization demo, not a medical assessment.',
      })
      updateRegionStatus(regionStatuses, region, severity)
    }
  }

  for (const alert of getValidatedRegionAlerts(regionAlerts)) {
    alerts.push({
      ...alert,
      id: `localized-${alert.region}`,
      measurement: 'Localized demo marker',
      explanation: 'This region alert was set explicitly for visualization testing; it is not inferred from vital signs.',
    })
    updateRegionStatus(regionStatuses, alert.region, alert.severity)
  }

  return { alerts, regionStatuses }
}
