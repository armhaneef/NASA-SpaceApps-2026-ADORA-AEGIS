import test from 'node:test'
import assert from 'node:assert/strict'
import {
  apiTimeoutMs,
  askAssistantQuestion,
  assistantTimeoutMs,
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

test('assistant chat uses the existing backend contract and preserves provider provenance', async () => {
  const originalFetch = globalThis.fetch
  let request
  globalThis.fetch = async (url, options) => {
    request = { url, options, body: JSON.parse(options.body) }
    return new Response(JSON.stringify({
      astronaut_id: 'AST-001',
      answer: 'The synthetic analysis reports a model finding.',
      assistant_version: 'member3-ai-assistant-0.1.0',
      is_mock: false,
      limitations: ['This is not medical advice.'],
      mode: 'local',
      status: 'completed',
      data_source: 'configured_local_provider',
      context: { analysis: null },
    }), { status: 200, headers: { 'Content-Type': 'application/json' } })
  }
  try {
    const response = await askAssistantQuestion(
      'AST-001',
      'What does this synthetic analysis show?',
      'local',
      17,
    )
    assert.equal(request.url, 'http://127.0.0.1:8000/ai/assistant')
    assert.deepEqual(request.body, {
      astronaut_id: 'AST-001',
      question: 'What does this synthetic analysis show?',
      mode: 'local',
      analysis_id: 17,
    })
    assert.equal(request.options.method, 'POST')
    assert.equal(request.options.signal.aborted, false)
    assert.equal(response.is_mock, false)
    assert.equal(response.answer, 'The synthetic analysis reports a model finding.')
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('assistant chat reports request timeouts distinctly', async () => {
  assert.equal(assistantTimeoutMs(), 90_000)
  const originalFetch = globalThis.fetch
  globalThis.fetch = (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true })
  })
  try {
    await assert.rejects(
      askAssistantQuestion('AST-001', 'Explain this finding.', 'local', null, { timeoutMs: 5 }),
      (error) => error.code === 'API_REQUEST_TIMEOUT',
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('assistant chat rejects an empty or malformed answer', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => new Response(JSON.stringify({
    answer: '  ',
    assistant_version: 'test',
    is_mock: false,
    limitations: ['Not medical advice.'],
  }), { status: 200, headers: { 'Content-Type': 'application/json' } })
  try {
    await assert.rejects(
      askAssistantQuestion('AST-001', 'Explain this finding.', 'local'),
      (error) => error.code === 'API_INVALID_RESPONSE',
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('assistant chat preserves explicit mock status and unknown analysis context', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => new Response(JSON.stringify({
    astronaut_id: 'AST-001', answer: 'Mock educational reply.', is_mock: true,
    assistant_version: 'mock-fixture', limitations: ['Not a diagnosis.'],
    mode: 'mock', status: 'mock', data_source: 'backend_mock', context: { analysis: null },
  }), { status: 200 })
  try {
    const result = await askAssistantQuestion('AST-001', 'Explain synthetic data.')
    assert.equal(result.is_mock, true)
    assert.equal(result.status, 'mock')
    assert.equal(result.context.analysis, null)
  } finally { globalThis.fetch = originalFetch }
})

test('assistant chat rejects identity and status mismatches', async () => {
  const originalFetch = globalThis.fetch
  const valid = {
    astronaut_id: 'AST-001', answer: 'Synthetic fixture.', is_mock: false,
    assistant_version: 'fixture', limitations: ['Not medical advice.'], mode: 'local', status: 'completed',
  }
  try {
    for (const defect of [{ astronaut_id: 'OTHER' }, { mode: 'mock' }, { status: 'mock' }]) {
      globalThis.fetch = async () => new Response(JSON.stringify({ ...valid, ...defect }), { status: 200 })
      await assert.rejects(askAssistantQuestion('AST-001', 'Explain synthetic data.', 'local'),
        (error) => error.code === 'API_INVALID_RESPONSE')
    }
  } finally { globalThis.fetch = originalFetch }
})

test('assistant server errors retain 503 and 504 without a mock success', async () => {
  const originalFetch = globalThis.fetch
  try {
    for (const status of [503, 504]) {
      globalThis.fetch = async () => new Response(JSON.stringify({ detail: `Assistant HTTP ${status}` }), { status })
      await assert.rejects(askAssistantQuestion('AST-001', 'Explain synthetic data.', 'local'),
        (error) => error.code === 'API_HTTP_ERROR' && error.status === status)
    }
  } finally { globalThis.fetch = originalFetch }
})
