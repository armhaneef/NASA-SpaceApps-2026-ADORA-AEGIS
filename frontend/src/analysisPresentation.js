export function getAnalysisFindings(analysis) {
  if (analysis?.anomaly_detected !== true) return []

  const measurements = Array.isArray(analysis.affected_measurements)
    && analysis.affected_measurements.length
    ? analysis.affected_measurements
    : ['Overall synthetic anomaly']
  const explanation = Array.isArray(analysis.explanations)
    ? analysis.explanations.filter((item) => typeof item === 'string' && item.trim()).join(' ')
    : ''

  return measurements.map((measurement) => ({
    id: `analysis-${analysis.id ?? 'latest'}-${measurement}`,
    region: null,
    scope: 'global',
    kind: 'model-finding',
    measurement,
    reason: explanation || 'The analysis flagged synthetic input data for review.',
    source: 'backend-ml-analysis',
  }))
}

export function getAnalysisStatusLabel(analysis) {
  if (!analysis) return 'NOT RUN'
  const status = typeof analysis.status === 'string'
    ? analysis.status.replaceAll('_', ' ').toUpperCase()
    : 'STATUS UNAVAILABLE'
  return analysis.is_mock ? `${status} · MOCK OUTPUT` : status
}

export function getAnalysisStatusTone(analysis) {
  if (!analysis) return 'no-data'
  if (analysis.anomaly_detected === true) return 'analysis'
  if (analysis.status === 'normal') return 'normal'
  return 'no-data'
}
