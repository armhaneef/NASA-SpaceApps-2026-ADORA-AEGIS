import assert from 'node:assert/strict'
import test from 'node:test'
import {
  getAnalysisFindings,
  getAnalysisStatusLabel,
  getAnalysisStatusTone,
} from '../src/analysisPresentation.js'

test('algorithmic findings stay global and carry no clinical severity', () => {
  const findings = getAnalysisFindings({
    id: 12,
    anomaly_detected: true,
    affected_measurements: ['heart_rate', 'spo2'],
    explanations: ['Synthetic values differed from the fitted model.'],
  })

  assert.equal(findings.length, 2)
  assert.ok(findings.every((finding) => finding.region === null))
  assert.ok(findings.every((finding) => finding.scope === 'global'))
  assert.ok(findings.every((finding) => finding.severity === undefined))
  assert.equal(getAnalysisStatusTone({ anomaly_detected: true }), 'analysis')
})

test('mock, normal, and insufficient-data analysis labels remain distinct', () => {
  assert.equal(getAnalysisStatusLabel({ status: 'normal', is_mock: false }), 'NORMAL')
  assert.equal(getAnalysisStatusLabel({ status: 'anomaly', is_mock: true }), 'ANOMALY · MOCK OUTPUT')
  assert.equal(getAnalysisStatusLabel({ status: 'insufficient_data', is_mock: false }), 'INSUFFICIENT DATA')
  assert.equal(getAnalysisStatusLabel(null), 'NOT RUN')
  assert.equal(getAnalysisStatusTone({ status: 'insufficient_data' }), 'no-data')
})

test('an anomaly without affected fields gets a global summary, not a region', () => {
  const findings = getAnalysisFindings({ anomaly_detected: true, affected_measurements: [] })
  assert.equal(findings.length, 1)
  assert.equal(findings[0].scope, 'global')
  assert.equal(findings[0].region, null)
  assert.equal(findings[0].measurement, 'Overall synthetic anomaly')
})
