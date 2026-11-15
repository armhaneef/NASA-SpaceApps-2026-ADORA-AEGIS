const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const DEFAULT_TIMEOUT_MS = 10_000
// Member 3 allows 60 s; the backend bridge allows 70 s. Leave browser headroom.
const ASSISTANT_TIMEOUT_MS = 90_000
const configuredTimeout = Number(import.meta.env?.VITE_API_TIMEOUT_MS)
const API_TIMEOUT_MS = Number.isFinite(configuredTimeout) && configuredTimeout > 0
  ? configuredTimeout
  : DEFAULT_TIMEOUT_MS

const SENSOR_FIELDS = {
  heart_rate: ['heart_rate_bpm', 'heart'],
  spo2: ['spo2_percent', 'oxygen'],
  respiration_rate: ['respiration_rate_bpm', 'respiration'],
  skin_temperature: ['skin_temperature_c', 'temperature'],
}

function isSyntheticReading(reading) {
  return reading?.is_simulated === true
    && typeof reading.source === 'string'
    && reading.source.toLowerCase().startsWith('synthetic')
}

export function filterSyntheticAstronauts(astronauts) {
  return (Array.isArray(astronauts) ? astronauts : []).filter((astronaut) => (
    typeof astronaut?.profile_metadata?.data_source === 'string'
    && astronaut.profile_metadata.data_source.toLowerCase().startsWith('synthetic')
  ))
}

export function normalizeLatestReadings(rows) {
  const result = {
    heart_rate_bpm: null,
    spo2_percent: null,
    respiration_rate_bpm: null,
    skin_temperature_c: null,
  }
  const sources = new Set()
  for (const row of Array.isArray(rows) ? rows : []) {
    if (!isSyntheticReading(row)) continue
    const target = SENSOR_FIELDS[row.measurement_type]?.[0]
    if (!target || !Number.isFinite(row.value)) continue
    result[target] = row.value
    sources.add(row.source)
  }
  return { readings: result, sources: [...sources] }
}

export function normalizeHistory(rows) {
  const byTimestamp = new Map()
  for (const row of Array.isArray(rows) ? rows : []) {
    if (!isSyntheticReading(row) || !Number.isFinite(row.value)) continue
    const mapping = SENSOR_FIELDS[row.measurement_type]
    if (!mapping) continue
    const [readingKey, historyKey] = mapping
    const point = byTimestamp.get(row.timestamp) ?? {
      time: new Date(row.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: row.timestamp,
      heart_rate_bpm: null,
      spo2_percent: null,
      respiration_rate_bpm: null,
      skin_temperature_c: null,
      heart: null,
      oxygen: null,
      respiration: null,
      temperature: null,
    }
    point[readingKey] = row.value
    point[historyKey] = row.value
    byTimestamp.set(row.timestamp, point)
  }
  return [...byTimestamp.values()].sort((a, b) => a.timestamp.localeCompare(b.timestamp))
}

function apiRequestError(message, code, cause) {
  const error = new Error(message, cause ? { cause } : undefined)
  error.code = code
  return error
}

export function isApiRequestCancelled(error) {
  return error?.code === 'API_REQUEST_CANCELLED'
}

async function request(path, options = {}) {
  const { signal: callerSignal, timeoutMs = API_TIMEOUT_MS, ...fetchOptions } = options
  const controller = new AbortController()
  let timedOut = false
  const abortFromCaller = () => controller.abort(callerSignal?.reason)
  if (callerSignal?.aborted) abortFromCaller()
  else callerSignal?.addEventListener('abort', abortFromCaller, { once: true })
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: { ...(fetchOptions.body ? { 'Content-Type': 'application/json' } : {}), ...fetchOptions.headers },
    })
    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try {
        const body = await response.json()
        if (typeof body.detail === 'string') detail = body.detail
      } catch {
        // Keep the status code when the server returns a non-JSON error page.
      }
      const error = apiRequestError(detail, 'API_HTTP_ERROR')
      error.status = response.status
      throw error
    }
    if (response.status === 204) return null
    try {
      return await response.json()
    } catch (error) {
      if (timedOut || callerSignal?.aborted) throw error
      throw apiRequestError('AEGIS API returned an unreadable response.', 'API_INVALID_RESPONSE', error)
    }
  } catch (error) {
    if (error?.code === 'API_HTTP_ERROR' || error?.code === 'API_INVALID_RESPONSE') throw error
    if (timedOut) {
      throw apiRequestError(`AEGIS API request timed out after ${timeoutMs} ms.`, 'API_REQUEST_TIMEOUT', error)
    }
    if (callerSignal?.aborted || controller.signal.aborted) {
      throw apiRequestError('AEGIS API request was cancelled.', 'API_REQUEST_CANCELLED', error)
    }
    throw apiRequestError(
      `Cannot reach the AEGIS API at ${API_BASE_URL}: ${error.message}`,
      'API_NETWORK_ERROR',
      error,
    )
  } finally {
    clearTimeout(timer)
    callerSignal?.removeEventListener('abort', abortFromCaller)
  }
}

export async function fetchSyntheticAstronauts(options = {}) {
  const astronauts = await request('/astronauts', options)
  return filterSyntheticAstronauts(astronauts)
}

export async function fetchLiveDashboard(astronautId, options = {}) {
  const query = new URLSearchParams({ limit: '100', offset: '0' })
  const measurements = Object.keys(SENSOR_FIELDS)
  const [latestRows, ...historyResults] = await Promise.all([
    request(`/health/${encodeURIComponent(astronautId)}/latest`, options),
    ...measurements.map((measurement) => request(
      `/health/${encodeURIComponent(astronautId)}/history?${query}&measurement_type=${measurement}`,
      options,
    )),
  ])
  let analysis = null
  try {
    analysis = await request(`/health/${encodeURIComponent(astronautId)}/analyses/latest`, options)
  } catch (error) {
    if (error.status !== 404) throw error
  }
  const normalized = normalizeLatestReadings(latestRows)
  const history = normalizeHistory(historyResults.flat())
  const analysisSources = latestRows
    .filter((row) => isSyntheticReading(row)
      && ['heart_rate', 'spo2', 'skin_temperature'].includes(row.measurement_type))
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
  return {
    ...normalized,
    history,
    analysis,
    source: analysisSources.at(-1)?.source ?? null,
    timestamp: latestRows.filter(isSyntheticReading).map((row) => row.timestamp).sort().at(-1) ?? null,
  }
}

export function runLocalAnalysis(astronautId, source, options = {}) {
  return request(`/health/${encodeURIComponent(astronautId)}/analyses`, {
    ...options,
    method: 'POST',
    body: JSON.stringify({ mode: 'local', source, history_limit: 100, temperature_is_skin: false }),
  })
}

export function askForExplanation(astronautId, analysisId, mode = 'mock', options = {}) {
  return askAssistantQuestion(astronautId,
    'Explain the latest synthetic analysis and state its limitations.', mode, analysisId, options)
}

export function askAssistantQuestion(astronautId, question, mode = 'mock', analysisId = null, options = {}) {
  return request('/ai/assistant', {
    ...options,
    timeoutMs: options.timeoutMs ?? ASSISTANT_TIMEOUT_MS,
    method: 'POST',
    body: JSON.stringify({
      astronaut_id: astronautId,
      question,
      mode,
      ...(analysisId == null ? {} : { analysis_id: analysisId }),
    }),
  }).then((response) => {
    if (!response
      || response.astronaut_id !== astronautId
      || response.mode !== mode
      || response.status !== (response.is_mock ? 'mock' : 'completed')
      || typeof response.answer !== 'string'
      || !response.answer.trim()
      || typeof response.is_mock !== 'boolean'
      || typeof response.assistant_version !== 'string'
      || !response.assistant_version.trim()
      || !Array.isArray(response.limitations)
      || response.limitations.length === 0
      || !response.limitations.every((limitation) => (
        typeof limitation === 'string' && limitation.trim().length > 0
      ))) {
      throw apiRequestError('AEGIS assistant returned an incomplete response.', 'API_INVALID_RESPONSE')
    }
    return response
  })
}

export function apiBaseUrl() {
  return API_BASE_URL
}

export function apiTimeoutMs() {
  return API_TIMEOUT_MS
}

export function assistantTimeoutMs() {
  return ASSISTANT_TIMEOUT_MS
}
