import test from 'node:test'
import assert from 'node:assert/strict'
import {
  apiTimeoutMs,
  fetchSyntheticAstronauts,
  filterSyntheticAstronauts,
  isApiRequestCancelled,
  normalizeHistory,
  normalizeLatestReadings,
} from '../src/api.js'

test('live profile list only exposes profiles marked synthetic', () => {
  const profiles = filterSyntheticAstronauts([
    { astronaut_id: 'AST-001', profile_metadata: { data_source: 'synthetic_data_engine' } },
    { astronaut_id: 'REAL-001', profile_metadata: {} },
  ])
  assert.deepEqual(profiles.map((profile) => profile.astronaut_id), ['AST-001'])
})

test('latest readings keep synthetic fields and omit body temperature semantics', () => {
  const result = normalizeLatestReadings([
    { measurement_type: 'heart_rate', value: 78, source: 'synthetic_fixture', is_simulated: true },
    { measurement_type: 'temperature', value: 36.8, source: 'synthetic_fixture', is_simulated: true },
    { measurement_type: 'spo2', value: 98, source: 'real_sensor', is_simulated: false },
  ])
  assert.equal(result.readings.heart_rate_bpm, 78)
  assert.equal(result.readings.spo2_percent, null)
  assert.equal(result.readings.skin_temperature_c, null)
  assert.deepEqual(result.sources, ['synthetic_fixture'])
})

test('explicit skin temperature is normalized without accepting generic temperature', () => {
  const latest = normalizeLatestReadings([
    { measurement_type: 'skin_temperature', value: 31.8, source: 'synthetic_fixture', is_simulated: true },
    { measurement_type: 'temperature', value: 37, source: 'synthetic_fixture', is_simulated: true },
  ])
  assert.equal(latest.readings.skin_temperature_c, 31.8)
  const history = normalizeHistory([
    { measurement_type: 'skin_temperature', value: 31.8, source: 'synthetic_fixture', is_simulated: true, timestamp: '2026-01-01T00:00:00Z' },
    { measurement_type: 'temperature', value: 37, source: 'synthetic_fixture', is_simulated: true, timestamp: '2026-01-01T00:00:00Z' },
  ])
  assert.equal(history[0].temperature, 31.8)
  assert.equal(apiTimeoutMs() > 0, true)
})

test('history groups exact timestamps and preserves missing values as null', () => {
  const result = normalizeHistory([
    { measurement_type: 'heart_rate', value: 78, source: 'synthetic_fixture', is_simulated: true, timestamp: '2026-01-01T00:00:00Z' },
    { measurement_type: 'spo2', value: 98, source: 'synthetic_fixture', is_simulated: true, timestamp: '2026-01-01T00:00:00Z' },
    { measurement_type: 'temperature', value: 36.8, source: 'synthetic_fixture', is_simulated: true, timestamp: '2026-01-01T00:00:00Z' },
  ])
  assert.equal(result.length, 1)
  assert.equal(result[0].heart, 78)
  assert.equal(result[0].oxygen, 98)
  assert.equal(result[0].temperature, null)
})

test('API timeout aborts the fetch and reports a distinct timeout error', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true })
  })
  try {
    await assert.rejects(fetchSyntheticAstronauts({ timeoutMs: 5 }), (error) => (
      error.code === 'API_REQUEST_TIMEOUT' && error.message.includes('timed out')
    ))
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('caller cancellation aborts the fetch and is distinguished from network errors', async () => {
  const originalFetch = globalThis.fetch
  const controller = new AbortController()
  globalThis.fetch = (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true })
  })
  try {
    const request = fetchSyntheticAstronauts({ signal: controller.signal })
    controller.abort()
    await assert.rejects(request, (error) => (
      isApiRequestCancelled(error) && error.message.includes('cancelled')
    ))
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('network failures have a user-facing API connectivity error', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => { throw new Error('offline') }
  try {
    await assert.rejects(fetchSyntheticAstronauts(), (error) => (
      error.code === 'API_NETWORK_ERROR' && error.message.includes('Cannot reach')
    ))
  } finally {
    globalThis.fetch = originalFetch
  }
})
