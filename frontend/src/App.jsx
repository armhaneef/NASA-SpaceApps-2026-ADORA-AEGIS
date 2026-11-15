import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Sparkles } from '@react-three/drei'
import * as THREE from 'three'
import AnatomyModel from './AnatomyModel.jsx'
import {
  createDemoSnapshot,
  DEMO_SCENARIOS,
  DEMO_THRESHOLDS,
  evaluateSyntheticAlerts,
  HEALTH_BASELINE,
} from './healthAlerts.js'
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  Crosshair,
  Heart,
  Maximize2,
  Minus,
  Moon,
  Move3D,
  Plus,
  RotateCcw,
  ScanLine,
  Shield,
  Signal,
  Sparkles as SparklesIcon,
  Wind,
  X,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from 'recharts'
import './App.css'
import {
  getAnalysisFindings,
  getAnalysisStatusLabel,
  getAnalysisStatusTone,
} from './analysisPresentation.js'
import usePrefersReducedMotion from './usePrefersReducedMotion.js'
import {
  apiBaseUrl,
  askForExplanation,
  fetchLiveDashboard,
  fetchSyntheticAstronauts,
  isApiRequestCancelled,
  runLocalAnalysis,
} from './api.js'

const REGIONS = {
  head: {
    name: 'Head',
    shortName: 'HEAD',
    code: 'ANATOMY-01',
    description: 'Educational view of the skull and named head structures.',
    explanation:
      'This is an educational anatomical view. The prototype does not provide head-specific sensor readings or a neurological assessment.',
  },
  brain: {
    name: 'Brain',
    shortName: 'BRAIN',
    code: 'ANATOMY-01B',
    description: 'The GLB contains separately named brain, brainstem, and cerebellum meshes.',
    explanation:
      'The brain meshes are shown for education only. This prototype does not measure brain activity or provide a neurological assessment.',
  },
  heart: {
    name: 'Cardiovascular',
    shortName: 'HEART',
    code: 'ANATOMY-02',
    description: 'Educational heart view with general simulated vital-sign context.',
    explanation:
      'The displayed heart rate is a synthetic demonstration value. It is not a direct measurement of this model or a medical assessment.',
  },
  leftLung: {
    name: 'Left lung',
    shortName: 'LEFT LUNG',
    code: 'ANATOMY-03L',
    description: 'Left lung mesh; respiratory readings provide general, non-localized context.',
    explanation:
      'SpO₂ and respiration are general synthetic vital signs shown for context; they are not left-lung measurements or a respiratory diagnosis.',
  },
  rightLung: {
    name: 'Right lung',
    shortName: 'RIGHT LUNG',
    code: 'ANATOMY-03R',
    description: 'Right lung mesh; respiratory readings provide general, non-localized context.',
    explanation:
      'SpO₂ and respiration are general synthetic vital signs shown for context; they are not right-lung measurements or a respiratory diagnosis.',
  },
  abdomen: {
    name: 'Abdomen',
    shortName: 'ABDOMEN',
    code: 'ANATOMY-04',
    description: 'Educational view of named abdominal organs in the model.',
    explanation:
      'The abdominal structures are shown for education. The general body-temperature display is not a localized abdominal measurement.',
  },
  leftArm: {
    name: 'Left arm',
    shortName: 'LEFT ARM',
    code: 'ANATOMY-05',
    description: 'Grouped left-side arm structures identified by their mesh names.',
    explanation: 'The selected arm meshes are anatomical context only. No arm-specific health measurements are available in this prototype.',
  },
  rightArm: {
    name: 'Right arm',
    shortName: 'RIGHT ARM',
    code: 'ANATOMY-06',
    description: 'Grouped right-side arm structures identified by their mesh names.',
    explanation: 'The selected arm meshes are anatomical context only. No arm-specific health measurements are available in this prototype.',
  },
  leftLeg: {
    name: 'Left leg',
    shortName: 'LEFT LEG',
    code: 'ANATOMY-07',
    description: 'Grouped left-side leg structures identified by their mesh names.',
    explanation: 'The selected leg meshes are anatomical context only. No leg-specific health measurements are available in this prototype.',
  },
  rightLeg: {
    name: 'Right leg',
    shortName: 'RIGHT LEG',
    code: 'ANATOMY-08',
    description: 'Grouped right-side leg structures identified by their mesh names.',
    explanation: 'The selected leg meshes are anatomical context only. No leg-specific health measurements are available in this prototype.',
  },
}

const METRIC_DEFINITIONS = [
  {
    name: 'Heart rate',
    shortName: 'Heart rate',
    readingKey: 'heart_rate_bpm',
    alertKey: 'heart_rate_bpm',
    unit: 'bpm',
    baseline: HEALTH_BASELINE.heart_rate_bpm,
    icon: Heart,
    color: '#ff7892',
    historyKey: 'heart',
  },
  {
    name: 'Oxygen saturation',
    shortName: 'SpO₂',
    readingKey: 'spo2_percent',
    alertKey: 'spo2_percent',
    unit: '%',
    baseline: HEALTH_BASELINE.spo2_percent,
    icon: Activity,
    color: '#71e7ff',
    historyKey: 'oxygen',
  },
  {
    name: 'Body temperature',
    shortName: 'Temp.',
    readingKey: 'body_temperature_c',
    unit: '°C',
    baseline: HEALTH_BASELINE.body_temperature_c,
    icon: Moon,
    color: '#ffbc77',
    historyKey: 'temperature',
  },
  {
    name: 'Respiration',
    shortName: 'Resp.',
    readingKey: 'respiration_rate_bpm',
    alertKey: 'respiration_rate_bpm',
    unit: '/min',
    baseline: HEALTH_BASELINE.respiration_rate_bpm,
    icon: Wind,
    color: '#8fa9ff',
    historyKey: 'respiration',
  },
]

const THRESHOLD_FIELDS = [
  { key: 'heart_rate_bpm', direction: 'high', label: 'Heart rate · high Δ' },
  { key: 'heart_rate_bpm', direction: 'low', label: 'Heart rate · low Δ' },
  { key: 'spo2_percent', direction: 'low', label: 'SpO₂ · low Δ' },
  { key: 'respiration_rate_bpm', direction: 'high', label: 'Respiration · high Δ' },
  { key: 'respiration_rate_bpm', direction: 'low', label: 'Respiration · low Δ' },
]

function getMetrics(readings, alerts, live = false) {
  return METRIC_DEFINITIONS.map((definition) => {
    const rawValue = readings[definition.readingKey]
    const present = Number.isFinite(rawValue)
    const value = !present
      ? '—'
      : definition.unit === '°C'
        ? rawValue.toFixed(1)
        : String(Math.round(rawValue))
    const difference = present ? rawValue - definition.baseline : null
    const change = !present || live
      ? '—'
      : definition.unit === '°C'
        ? `${difference > 0 ? '+' : ''}${difference.toFixed(1)}`
        : `${difference > 0 ? '+' : ''}${Math.round(difference)}`

    return {
      ...definition,
      name: live && definition.readingKey === 'body_temperature_c' ? 'Skin temperature' : definition.name,
      value,
      baselineLabel: live ? 'NOT PROVIDED' : `${definition.baseline}${definition.unit === '°C' ? ' °C' : ` ${definition.unit}`}`,
      change,
      status: live || !present || !definition.alertKey
        ? 'no-data'
        : alerts.find((alert) => alert.measurementKey === definition.alertKey)?.severity ?? 'normal',
    }
  })
}

function getDemoHistory(readings) {
  return Array.from({ length: 28 }, (_, index) => {
    const wave = (offset, magnitude, frequency) =>
      offset + Math.sin(index * frequency) * magnitude + Math.cos(index * 0.37) * magnitude * 0.28

    return {
      time: `${String(Math.floor(index / 2)).padStart(2, '0')}:${index % 2 ? '30' : '00'}`,
      heart: wave(readings.heart_rate_bpm, 4.3, 0.75),
      oxygen: wave(readings.spo2_percent, 0.9, 0.53),
      temperature: wave(readings.body_temperature_c, 0.16, 0.3),
      respiration: wave(readings.respiration_rate_bpm, 1.6, 0.9),
    }
  })
}

function ProjectionPlatform({ animate }) {
  const rings = useRef([])
  useFrame(({ clock }) => {
    if (!animate) return
    rings.current.forEach((ring, index) => {
      if (ring) ring.rotation.z = clock.elapsedTime * (index % 2 ? -0.08 : 0.08)
    })
  })

  return (
    <group position={[0, -1.72, 0]}>
      {[1.08, 1.31, 1.58, 1.83].map((radius, index) => (
        <mesh key={radius} ref={(node) => (rings.current[index] = node)} rotation-x={-Math.PI / 2}>
          <ringGeometry args={[radius, radius + (index === 0 ? 0.015 : 0.006), 112]} />
          <meshBasicMaterial
            color={index === 0 ? '#a7f8ff' : '#2c92b6'}
            transparent
            opacity={index === 0 ? 0.78 : index === 1 ? 0.34 : 0.2}
            side={2}
          />
        </mesh>
      ))}
      {Array.from({ length: 48 }, (_, index) => {
        const angle = (index / 48) * Math.PI * 2
        const radius = index % 4 === 0 ? 1.72 : 1.76
        return (
          <mesh
            key={index}
            position={[Math.cos(angle) * radius, 0, Math.sin(angle) * radius]}
            rotation-y={-angle}
          >
            <boxGeometry args={[index % 4 === 0 ? 0.07 : 0.035, 0.008, 0.12]} />
            <meshBasicMaterial color="#6bd8ec" transparent opacity={index % 4 === 0 ? 0.56 : 0.24} />
          </mesh>
        )
      })}
      <mesh rotation-x={-Math.PI / 2} position-y={-0.035}>
        <circleGeometry args={[1.08, 80]} />
        <meshBasicMaterial color="#1e90ae" transparent opacity={0.1} />
      </mesh>
      <mesh position-y={-0.08}>
        <cylinderGeometry args={[1.05, 1.24, 0.1, 80, 1, false]} />
        <meshBasicMaterial color="#338da5" transparent opacity={0.1} />
      </mesh>
    </group>
  )
}

function ScanBeam({ active }) {
  const beam = useRef()
  useFrame(({ clock }) => {
    if (beam.current) beam.current.position.y = -1.9 + ((clock.elapsedTime * 0.55) % 3.8)
  })

  if (!active) return null

  return (
    <group ref={beam} position={[0, -1.8, 0]}>
      <mesh>
        <planeGeometry args={[3.5, 0.09]} />
        <meshBasicMaterial
          color="#76eaff"
          transparent
          opacity={0.07}
          side={2}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      <mesh position={[0, 0, 0.01]}>
        <planeGeometry args={[3.5, 0.008]} />
        <meshBasicMaterial color="#c0fbff" transparent opacity={0.38} side={2} />
      </mesh>
    </group>
  )
}

function CameraFocus({ controlsRef, selected, focusPoints, reducedMotion }) {
  const focusTarget = useRef(new THREE.Vector3(0, 0, 0))
  const previousSelection = useRef(selected)
  const transitionDistance = useRef(5.8)
  const isTransitioning = useRef(false)

  useFrame((_, delta) => {
    const controls = controlsRef.current
    if (!controls) return

    if (previousSelection.current !== selected) {
      previousSelection.current = selected
      const point = focusPoints[selected]
      focusTarget.current.fromArray(point ?? [0, 0, 0])
      const regionDistance = {
        brain: 3.2,
        head: 3.35,
        heart: 3.35,
        leftLung: 3.45,
        rightLung: 3.45,
        abdomen: 3.55,
        leftArm: 3.65,
        rightArm: 3.65,
        leftLeg: 3.75,
        rightLeg: 3.75,
      }
      transitionDistance.current = selected && point ? regionDistance[selected] ?? 3.5 : 5.8
      isTransitioning.current = true
    }

    if (!isTransitioning.current) return

    const smoothing = 1 - Math.exp(-delta * 2.8)
    const direction = controls.object.position.clone().sub(controls.target).normalize()
    if (direction.lengthSq() === 0) direction.set(0, 0, 1)

    if (reducedMotion) {
      controls.target.copy(focusTarget.current)
      controls.object.position.copy(
        controls.target.clone().addScaledVector(direction, transitionDistance.current),
      )
      controls.update()
      isTransitioning.current = false
      return
    }

    controls.target.lerp(focusTarget.current, smoothing)
    const cameraPosition = controls.target
      .clone()
      .addScaledVector(direction, transitionDistance.current)
    controls.object.position.lerp(cameraPosition, smoothing)
    controls.update()

    if (
      controls.target.distanceToSquared(focusTarget.current) < 0.00001
      && Math.abs(controls.object.position.distanceTo(controls.target) - transitionDistance.current) < 0.02
    ) {
      isTransitioning.current = false
    }
  })
  return null
}

function DigitalHuman({
  mode,
  layer,
  selected,
  scan,
  regionStatuses,
  controlsRef,
  focusPoints,
  onSelect,
  onModelStatusChange,
  onModelInfo,
  retryModelKey,
  reducedMotion,
}) {
  return (
    <Canvas
      frameloop={reducedMotion ? 'demand' : 'always'}
      camera={{ position: [0, 0.02, 5.8], fov: 40, near: 0.1, far: 100 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true }}
      onPointerMissed={() => onSelect(null)}
      aria-label="Interactive 3D anatomy. Use the region selector to navigate without a pointer."
    >
      <color attach="background" args={['#040b12']} />
      <fog attach="fog" args={['#040b12', 8, 17]} />
      <ambientLight intensity={0.6} color="#8cdfff" />
      <hemisphereLight args={['#8cecff', '#06111e', 1.1]} />
      <pointLight position={[0, 2.5, 3]} intensity={18} color="#65e6ff" distance={9} />
      <pointLight position={[-3, 0, -2]} intensity={15} color="#316eff" distance={8} />
      <pointLight position={[3, -1, 1]} intensity={12} color="#39c7df" distance={7} />
      <pointLight position={[0, -1.7, 0]} intensity={4} color="#61eaff" distance={4} />
      <mesh position={[0, 0, -0.5]} renderOrder={0}>
        <cylinderGeometry args={[0.8, 1.42, 4.2, 48, 1, true]} />
        <meshBasicMaterial
          color="#36bce5"
          transparent
          opacity={0.035}
          side={THREE.DoubleSide}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      {!reducedMotion && <Sparkles count={42} scale={[4.5, 5.2, 3.5]} size={2} speed={0.12} opacity={0.42} color="#85eaff" />}
      <AnatomyModel
        key={retryModelKey}
        mode={mode}
        layer={layer}
        selected={selected}
        regionStatuses={regionStatuses}
        onSelect={onSelect}
        onStatusChange={onModelStatusChange}
        onModelInfo={onModelInfo}
        reducedMotion={reducedMotion}
      />
      <ProjectionPlatform animate={!reducedMotion} />
      <ScanBeam active={scan && !reducedMotion} />
      <CameraFocus controlsRef={controlsRef} selected={selected} focusPoints={focusPoints} reducedMotion={reducedMotion} />
      <OrbitControls
        ref={controlsRef}
        makeDefault
        enablePan
        enableDamping
        dampingFactor={0.08}
        minDistance={1.7}
        maxDistance={9}
        minPolarAngle={Math.PI * 0.29}
        maxPolarAngle={Math.PI * 0.68}
        rotateSpeed={0.65}
      />
    </Canvas>
  )
}

function MetricCard({ metric, index, active, onSelect, live }) {
  const Icon = metric.icon
  const positive = metric.change.startsWith('+')

  return (
    <button
      type="button"
      className={`metric-readout ${active ? 'metric-active' : ''} metric-status-${metric.status}`}
      onClick={onSelect}
      aria-pressed={active}
      aria-label={`Show ${live ? 'synthetic API' : 'synthetic demo'} history for ${metric.name}`}
      style={{ '--metric-color': metric.color, '--stagger': `${index * 70}ms` }}
    >
      <div className="metric-topline">
        <span className="metric-icon"><Icon size={14} strokeWidth={1.7} /></span>
        <span className="metric-name">{live && metric.readingKey === 'body_temperature_c' ? 'Skin temp' : metric.shortName}</span>
        <span className="metric-live"><i />{live ? 'API' : 'SIM'}</span>
      </div>
      <div className="metric-number">
        <strong>{metric.value}</strong>
        <span>{metric.unit}</span>
      </div>
      <div className="metric-baseline">
        <span>{live ? 'BASELINE' : 'DEMO REF'} {metric.baselineLabel}</span>
        <span className={positive ? 'trend-up' : 'trend-down'}>
          {metric.change !== '—' && (positive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />)}
          {metric.change}
        </span>
      </div>
    </button>
  )
}

function EcgChart({ metric, history, live }) {
  return (
    <div className="chart-frame">
      <div className="chart-heading">
        <div>
          <span className="eyebrow">{live ? 'BACKEND HISTORY' : 'SIMULATED FEED'}</span>
          <strong><Activity size={13} /> {metric.name.toUpperCase()}</strong>
        </div>
        <span className="chart-window">{live ? 'API WINDOW' : 'DEMO WINDOW'}</span>
      </div>
      <div className="chart-canvas">
        {history.length ? <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 8, right: 2, left: -26, bottom: 0 }}>
            <defs>
              <linearGradient id="telemetry-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={metric.color} stopOpacity={0.26} />
                <stop offset="95%" stopColor={metric.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(104, 188, 207, .1)" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fill: '#597784', fontSize: 8 }}
              axisLine={false}
              tickLine={false}
              interval={8}
            />
            <Tooltip
              contentStyle={{
                background: '#07151e',
                border: '1px solid rgba(108, 217, 240, .24)',
                borderRadius: 4,
                color: '#e8faff',
                fontSize: 10,
              }}
              labelStyle={{ color: '#89a8b2' }}
              formatter={(value) => [`${Number(value).toFixed(metric.unit === '°C' ? 1 : 0)} ${metric.unit}`, metric.name]}
            />
            <Area
              type="monotone"
              dataKey={metric.historyKey}
              stroke={metric.color}
              strokeWidth={1.8}
              fill="url(#telemetry-fill)"
              isAnimationActive={false}
              dot={false}
              activeDot={{ r: 3, fill: metric.color, stroke: '#08141b', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer> : <p className="chart-empty">{live ? 'No synthetic history is available for this reading.' : 'No demo history is available.'}</p>}
      </div>
      <div className="chart-footnote">
        <span>{live ? 'NO BASELINE PROVIDED' : 'DEMO REFERENCE'}</span>
        {!live && <span className="baseline-key" />}
        <span>{live ? 'SYNTHETIC API DATA' : 'SIMULATED SIGNAL'}</span>
      </div>
    </div>
  )
}

function Header({ astronaut, setAstronaut, hasAlerts, live, astronauts, analysis }) {
  return (
    <header className="topbar">
      <div className="brand-lockup">
        <div className="adora-mark"><span /><span /><span /></div>
        <div className="brand-name">ADORA<span> / AEGIS</span></div>
        <div className="brand-divider" />
        <div className="vital-brand">powered by <b>VitalTwin</b></div>
      </div>
      <div className="mission-lockup">
        <span className="eyebrow">AEGIS PROTOTYPE <b>/</b> EDUCATIONAL DEMO</span>
        <strong>SYNTHETIC HEALTH DASHBOARD</strong>
      </div>
      <div className="topbar-right">
        <label className="select-wrap">
          <span>CREW</span>
          <select value={astronaut} onChange={(event) => setAstronaut(event.target.value)} aria-label="Select synthetic astronaut">
            {(live ? astronauts.length
              ? astronauts.map((item) => ({ id: item.astronaut_id, label: item.astronaut_id }))
              : [{ id: '', label: 'NO SYNTHETIC PROFILE' }]
              : [
              { id: 'A-01', label: 'ASTRONAUT A-01' },
              { id: 'A-02', label: 'ASTRONAUT A-02' },
              { id: 'A-03', label: 'ASTRONAUT A-03' },
            ]).map((item) => <option key={item.id || 'empty'} value={item.id}>{item.label}</option>)}
          </select>
          <ChevronDown size={12} />
        </label>
        <div className={`system-state ${!live && hasAlerts ? 'system-state-alert' : ''} ${live && analysis?.anomaly_detected === true ? 'system-state-review' : ''}`}>
          <i /><span>{live ? 'API ANALYSIS' : 'DEMO STATUS'}<br /><b>{live
            ? getAnalysisStatusLabel(analysis)
            : hasAlerts ? 'ALERTS ACTIVE' : 'NO ACTIVE ALERTS'}</b></span>
        </div>
        <div className="synthetic-tag"><span /> SYNTHETIC EDUCATIONAL DEMO <b>/</b> {live ? 'LIVE API' : 'SIMULATION'}</div>
      </div>
    </header>
  )
}

function LeftHud({
  astronaut,
  activeMetric,
  setActiveMetric,
  metrics,
  history,
  scenarioId,
  onScenarioChange,
  thresholds,
  onThresholdChange,
  live,
  onModeChange,
  liveStatus,
  liveError,
  liveTimestamp,
  onRetryLive,
  onRunAnalysis,
  analysisLoading,
}) {
  const active = metrics[activeMetric]
  return (
    <aside className="left-hud">
      <div className="panel-title">
        <div><span className="panel-index">01</span><span>CREW VITALS</span></div>
        <span className="feed-state"><i /> {live ? 'SYNTHETIC API' : 'SIMULATED FEED'}</span>
      </div>
      <div className="data-mode-control" role="group" aria-label="Dashboard data mode">
        <button type="button" className={!live ? 'control-active' : ''} aria-pressed={!live} onClick={() => onModeChange('demo')}>DEMO MODE</button>
        <button type="button" className={live ? 'control-active' : ''} aria-pressed={live} onClick={() => onModeChange('live')}>LIVE API MODE</button>
      </div>
      <div className="crew-profile">
        <div className="crew-avatar">A<span>{astronaut.slice(-2)}</span></div>
        <div className="crew-details">
          <strong>SYNTHETIC PROFILE {astronaut || '—'}</strong>
          <span>EDUCATIONAL DATA ONLY</span>
        </div>
        <div className="crew-signal"><Signal size={15} /></div>
      </div>
      {!live ? <label className="scenario-picker">
        <span>SIMULATION / DEMO MODE</span>
        <select
          value={scenarioId}
          onChange={(event) => onScenarioChange(event.target.value)}
          aria-label="Select synthetic health alert scenario"
        >
          {DEMO_SCENARIOS.map((scenario) => (
            <option key={scenario.id} value={scenario.id}>{scenario.label}</option>
          ))}
        </select>
      </label> : (
        <section className={`api-connection api-connection-${liveStatus}`} aria-live="polite">
          <span>LIVE BACKEND · SYNTHETIC DATA ONLY</span>
          <b>{liveStatus === 'loading' ? 'LOADING API DATA' : liveStatus === 'error' ? 'API ERROR' : liveStatus === 'empty' ? 'NO SYNTHETIC PROFILE' : 'CONNECTED'}</b>
          <small>{liveError || (liveStatus === 'empty' ? 'Create a marked synthetic astronaut and ingest synthetic readings first.' : `API ${apiBaseUrl()}${liveTimestamp ? ` · ${new Date(liveTimestamp).toLocaleString()}` : ''}`)}</small>
          <button type="button" className="api-retry-button" onClick={onRetryLive} disabled={liveStatus === 'loading'}>
            {liveStatus === 'ready' ? 'REFRESH LIVE DATA' : liveStatus === 'loading' ? 'CONNECTING…' : 'RETRY CONNECTION'}
          </button>
          <button type="button" className="analysis-button" onClick={onRunAnalysis} disabled={analysisLoading || liveStatus !== 'ready'}>
            {analysisLoading ? 'RUNNING LOCAL ML…' : 'RUN LOCAL ML ANALYSIS'}
          </button>
        </section>
      )}
      {!live && <details className="threshold-editor">
        <summary>CONFIGURE DEMO THRESHOLDS <span>Δ FROM BASELINE</span></summary>
        <div className="threshold-fields">
          {THRESHOLD_FIELDS.map(({ key, direction, label }) => (
            <div className="threshold-field" key={`${key}-${direction}`}>
              <span>{label}</span>
              <label>
                <span>WARN</span>
                <input
                  type="number"
                  min="1"
                  value={thresholds[key][direction].warning}
                  onChange={(event) => onThresholdChange(key, direction, 'warning', event.target.value)}
                  aria-label={`${label} warning deviation`}
                />
              </label>
              <label>
                <span>CRIT</span>
                <input
                  type="number"
                  min="1"
                  value={thresholds[key][direction].critical}
                  onChange={(event) => onThresholdChange(key, direction, 'critical', event.target.value)}
                  aria-label={`${label} critical deviation`}
                />
              </label>
            </div>
          ))}
        </div>
        <p>Illustrative deviation values; not clinical limits.</p>
      </details>}
      <div className="metrics-stack">
        {metrics.map((metric, index) => (
          <MetricCard
            key={metric.name}
            metric={metric}
            index={index}
            active={activeMetric === index}
            live={live}
            onSelect={() => setActiveMetric(index)}
          />
        ))}
      </div>
      <EcgChart metric={active} history={history} live={live} />
      <div className="baseline-note">
        <span className="baseline-symbol"><Crosshair size={13} /></span>
        <span>{live ? <>Backend values only<br /><b>No baseline interpretation</b></> : <>Values compared to <b>demo references</b><br />Synthetic illustration · 14h span</>}</span>
        <CircleHelp size={13} className="help-icon" />
      </div>
    </aside>
  )
}

function RightHud({
  selected,
  readings,
  alerts,
  regionStatuses,
  onSelectRegion,
  updatedAt,
  mobileOpen,
  onClose,
  mobileView,
  triggerRef,
  live,
  analysis,
  assistant,
  assistantStatus,
}) {
  const panelRef = useRef(null)
  const wasOpen = useRef(false)
  const region = selected ? REGIONS[selected] : null

  useEffect(() => {
    if (!mobileView) {
      wasOpen.current = mobileOpen
      return
    }
    if (mobileOpen) panelRef.current?.focus()
    else if (wasOpen.current) triggerRef.current?.focus()
    wasOpen.current = mobileOpen
  }, [mobileOpen, mobileView, triggerRef])

  useEffect(() => {
    if (!mobileView || !mobileOpen) return undefined
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [mobileOpen, mobileView, onClose])

  const trapDrawerTab = (event) => {
    if (event.key !== 'Tab' || !mobileView || !mobileOpen) return
    const focusable = panelRef.current?.querySelectorAll(
      'button:not(:disabled), select:not(:disabled), input:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])',
    )
    if (!focusable?.length) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (document.activeElement === panelRef.current) {
      event.preventDefault()
      const target = event.shiftKey ? last : first
      target.focus()
    } else if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }
  const demoStatus = alerts.some((alert) => alert.severity === 'critical')
    ? 'critical'
    : alerts.length
      ? 'warning'
      : 'normal'
  const status = selected
    ? regionStatuses[selected]
    : live ? getAnalysisStatusTone(analysis) : demoStatus
  const statusLabel = selected
    ? status.toUpperCase()
    : live ? getAnalysisStatusLabel(analysis) : alerts.length ? status.toUpperCase() : 'NO ACTIVE ALERTS'
  const regionalAlerts = alerts.filter((alert) => alert.region === selected)
  const visibleAlerts = alerts
  const indicators = live
    ? selected
      ? [
        ['Region status', 'NO DATA', 'No region-specific sensor was supplied'],
        ['Direct measurements', 'None', 'Global readings are not localized'],
      ]
      : [
        ['ML analysis', getAnalysisStatusLabel(analysis), analysis?.is_mock ? 'Explicit mock output' : 'Synthetic inputs only'],
        ['Affected measurements', analysis?.affected_measurements?.join(', ') || 'None reported', 'No anatomical mapping is inferred'],
        ['Data source', analysis?.data_source ?? 'Synthetic API', 'No NASA telemetry'],
      ]
    : selected === 'heart'
    ? [
        ['Heart rate', `${readings.heart_rate_bpm} bpm`, 'General synthetic reading · not heart-localized'],
        ['Baseline difference', `${readings.heart_rate_bpm - HEALTH_BASELINE.heart_rate_bpm >= 0 ? '+' : ''}${readings.heart_rate_bpm - HEALTH_BASELINE.heart_rate_bpm} bpm`, 'Demo reference comparison only'],
      ['Trend window', '28 demo points', 'Illustrative series; no prediction'],
    ]
    : ['leftLung', 'rightLung'].includes(selected)
      ? [
        ['SpO₂', `${readings.spo2_percent}%`, 'General synthetic reading · not lung-localized'],
        ['Respiration', `${readings.respiration_rate_bpm} /min`, 'General synthetic reading · not lung-localized'],
          ['Demo references', `${HEALTH_BASELINE.spo2_percent}% · ${HEALTH_BASELINE.respiration_rate_bpm} /min`, 'Illustrative comparison values'],
        ['Trend window', '28 demo points', 'Illustrative series; no prediction'],
      ]
      : selected
        ? [
          ['Region status', status === 'no-data' ? 'NO DATA' : status.toUpperCase(), 'No local sensor is represented'],
          ['Direct measurements', 'None', 'Anatomy display only'],
        ]
        : [
          ['Active demo alerts', String(alerts.length), 'Threshold and explicit demo markers'],
          ['Data source', 'Synthetic', 'No live astronaut connection'],
        ]
  const alertCountLabel = String(alerts.length).padStart(2, '0')

  return (
    <aside
      id="region-details-panel"
      ref={panelRef}
      className={`right-hud ${mobileOpen ? 'mobile-open' : ''}`}
      aria-label="Region health details"
      role={mobileView && mobileOpen ? 'dialog' : undefined}
      aria-modal={mobileView && mobileOpen ? 'true' : undefined}
      aria-hidden={mobileView && !mobileOpen ? 'true' : undefined}
      tabIndex={mobileView && mobileOpen ? -1 : undefined}
      onKeyDown={trapDrawerTab}
    >
      <div className="panel-title">
        <div><span className="panel-index">02</span><span>REGION ANALYSIS</span></div>
        <button type="button" className="mobile-drawer-close" onClick={onClose} aria-label="Close region details">
          <X size={16} />
        </button>
        <Maximize2 size={13} className="muted-icon desktop-maximize" />
      </div>
      <div className="region-overview">
        <div className={`region-orb ${selected ? `orb-${selected}` : ''}`}>
          <span className="orb-ring" />
          <span className="orb-core"><Activity size={21} /></span>
        </div>
        <div>
          <span className="eyebrow">{region?.code ?? 'FULL BODY SCAN'}</span>
          <h2>{region?.name ?? 'System overview'}</h2>
          <p>{region?.description ?? 'Select a highlighted region or choose a simulation scenario.'}</p>
        </div>
      </div>
      <div className="section-rule"><span>REGIONAL INDICATORS</span><i /></div>
      <div className="regional-metrics">
        {indicators.map(([label, value, note]) => (
          <div className="regional-metric" key={label}>
            <div className="regional-label">
              {label}
              {(selected || label === 'Active demo alerts' || (live && label === 'ML analysis')) && (
                <span className={`region-status-chip status-${status}`}>{statusLabel}</span>
              )}
            </div>
            <strong>{value}</strong>
            <span className="regional-note">{note}</span>
          </div>
        ))}
      </div>
      <section className={`region-detail-panel status-${status}`} aria-label="Selected region health details">
        <div className="region-detail-heading">
          <span>{selected ? 'REGION HEALTH STATUS' : live ? 'OVERALL API ANALYSIS' : 'OVERALL DEMO STATUS'}</span>
          <b>{statusLabel}</b>
        </div>
        <div className="region-detail-section">
          <span>{live ? 'GLOBAL ANALYSIS FINDINGS' : 'SIMULATED FINDINGS'}</span>
          {regionalAlerts.length ? (
            <ul>
              {regionalAlerts.map((alert) => <li key={alert.id}>{alert.reason}</li>)}
            </ul>
          ) : (
            <p>{selected
              ? live ? 'Global findings are not assigned to anatomical regions.' : 'No region-specific synthetic finding is available for this anatomical area.'
              : 'No region is selected. Scenario alerts remain visible below.'}</p>
          )}
        </div>
        <div className="region-detail-section">
          <span>TREND / SUGGESTED NEXT STEP</span>
          <p>
            {live
              ? 'Anomaly findings describe sensor data only. They do not localize a condition or provide a diagnosis.'
              : regionalAlerts.some((alert) => alert.source === 'demo-region-simulation')
              ? 'Review this explicit regional demo marker and the synthetic dashboard trends; no medical action is implied.'
              : 'Review the synthetic trend display for demonstration only. No predictive or clinical recommendation is available.'}
          </p>
        </div>
        <div className="region-detail-updated">
          {live ? 'API DATA UPDATED' : 'SIMULATION UI UPDATED'} · {updatedAt.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          })}
        </div>
      </section>
      <div className={`ml-status demo-rule-status status-${status}`}>
        <div className="ml-icon"><Activity size={17} /></div>
        <div className="ml-copy">
          <span className="eyebrow">{live ? 'BACKEND ML ANALYSIS' : 'DEMO THRESHOLD SCREEN'}</span>
          <strong><i /> {live ? getAnalysisStatusLabel(analysis) : alerts.length ? `${alerts.length} SIMULATED ALERT${alerts.length === 1 ? '' : 'S'}` : 'NO DEMO ALERTS'}</strong>
        </div>
        <span className="ml-score">{live ? analysis?.is_mock ? 'MOCK' : analysis?.model_version ?? '—' : 'RULES'}</span>
      </div>
      <div className="assistant-panel">
        <div className="assistant-heading">
          <span className="assistant-spark"><SparklesIcon size={13} /></span>
          <div><span className="eyebrow">{live ? 'BACKEND ASSISTANT' : 'AEGIS DEMO EXPLANATION'}</span><b>{live ? assistantStatus : 'Threshold context'}</b></div>
          <span className="assistant-beta">BETA</span>
        </div>
        <p>
          {live
            ? assistant?.answer ?? 'Run a local analysis to request an explanation. Offline fallback remains explicitly labelled.'
            : regionalAlerts[0]?.explanation
            ?? region?.explanation
            ?? 'Rule-based visual demo only. No ML model, backend alert service, live astronaut data, or clinical assessment is connected.'}
        </p>
        {live && assistant?.is_mock && <p className="assistant-fallback-note">Mock fallback: no assistant model was invoked.</p>}
        <span className="assistant-disclaimer"><Shield size={11} /> SYNTHETIC EDUCATIONAL DEMO · NOT A DIAGNOSIS</span>
      </div>
      <div className="alerts-heading">
        <span>{live ? 'ANALYSIS FINDINGS' : 'SIMULATED ALERTS'}</span><span>{alertCountLabel}</span>
      </div>
      <div className="alert-legend" aria-label="Alert color legend">
        {live ? <>
          <span><i className="legend-normal" />NORMAL MODEL STATUS</span>
          <span><i className="legend-analysis" />MODEL FINDING</span>
          <span><i className="legend-no-data" />NOT ASSESSED</span>
        </> : <>
          <span><i className="legend-normal" />NORMAL</span>
          <span><i className="legend-warning" />WARNING</span>
          <span><i className="legend-critical" />CRITICAL</span>
          <span><i className="legend-no-data" />NO DATA</span>
        </>}
      </div>
      {visibleAlerts.length ? visibleAlerts.map((alert) => (
        <button
          className={`alert-item ${alert.severity ? `alert-item-${alert.severity}` : 'alert-item-analysis'}`}
          key={alert.id}
          onClick={() => alert.region && onSelectRegion(alert.region)}
          type="button"
          disabled={!alert.region}
        >
          <span className="alert-mark"><AlertTriangle size={11} /></span>
          <span className="alert-copy">
            <b>{REGIONS[alert.region]?.name ?? (alert.region ?? 'GLOBAL')} · {alert.measurement}</b>
            <span>
              {alert.value === undefined
                ? alert.reason
                : `${alert.value} ${alert.unit} · baseline ${alert.baseline} ${alert.unit} · Δ ${alert.deviation > 0 ? '+' : ''}${alert.deviation}`}
            </span>
          </span>
          <span className="alert-type">{alert.severity?.toUpperCase() ?? 'MODEL FINDING'}</span>
        </button>
      )) : (
        <p className="no-alerts">{live ? 'No anomaly findings are available. Run local analysis after ingesting synthetic history.' : 'No active alerts in this synthetic scenario.'}</p>
      )}
      <p className="alert-disclaimer">{live ? 'Analysis output is synthetic and not a diagnosis. No anatomical localization is performed.' : 'Synthetic educational demo only. Global vital-sign alerts are not localized; only explicit regional demo markers highlight anatomy.'}</p>
    </aside>
  )
}

function ViewControls({
  mode,
  layer,
  setLayer,
  setMode,
  labels,
  setLabels,
  scan,
  setScan,
  resetCamera,
  zoomCamera,
  selected,
  focusPoints,
  onSelectRegion,
}) {
  return (
    <div className="view-controls">
      <div className="view-control-label"><span>HOLOGRAM VIEW</span><i /></div>
      <div className="control-group camera-controls" role="group" aria-label="3D camera controls">
        <button type="button" onClick={resetCamera} title="Reset camera" aria-label="Reset camera"><RotateCcw size={14} /><span>RESET</span></button>
        <i />
        <button type="button" onClick={() => zoomCamera(0.82)} title="Zoom in" aria-label="Zoom in"><Plus size={15} /></button>
        <button type="button" onClick={() => zoomCamera(1.22)} title="Zoom out" aria-label="Zoom out"><Minus size={15} /></button>
      </div>
      <div className="control-group mode-controls" role="group" aria-label="Body display mode">
        {[
          ['outer', 'OUTER'],
          ['wireframe', 'WIRE'],
          ['anatomy', 'ANATOMY'],
        ].map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={mode === value ? 'control-active' : ''}
            aria-pressed={mode === value}
            onClick={() => setMode(value)}
          >
            {value === 'wireframe' ? <Move3D size={13} /> : value === 'anatomy' ? <Activity size={13} /> : <ScanLine size={13} />}
            {label}
          </button>
        ))}
      </div>
      <div className="control-group layer-controls" role="group" aria-label="Anatomical layer">
        {[
          ['full', 'FULL BODY'],
          ['skeleton', 'SKELETON'],
          ['muscles', 'MUSCLES'],
          ['organs', 'ORGANS'],
        ].map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={layer === value ? 'control-active' : ''}
            aria-pressed={layer === value}
            onClick={() => setLayer(value)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="control-group toggles">
        <button type="button" className={labels ? 'toggle-on' : ''} onClick={() => setLabels(!labels)} title="Toggle labels" aria-label="Show anatomy labels" aria-pressed={labels}>
          <span className="toggle-switch"><i /></span><span>LABELS</span>
        </button>
        <button type="button" className={scan ? 'toggle-on' : ''} onClick={() => setScan(!scan)} title="Toggle scan effect" aria-label="Show scan animation" aria-pressed={scan}>
          <span className="toggle-switch"><i /></span><span>SCAN</span>
        </button>
      </div>
      <label className="region-picker">
        <span>ANATOMICAL REGION</span>
        <select
          value={selected ?? ''}
          onChange={(event) => onSelectRegion(event.target.value || null)}
          aria-label="Select anatomical region"
        >
          <option value="">FULL BODY</option>
          {Object.entries(REGIONS).map(([key, region]) => (
            <option key={key} value={key} disabled={!focusPoints[key]}>
              {region.shortName}
            </option>
          ))}
        </select>
      </label>
      <div className="drag-hint"><Move3D size={13} /><span>DRAG TO ROTATE</span></div>
    </div>
  )
}

function App() {
  const [appMode, setAppMode] = useState('demo')
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [modelInfo, setModelInfo] = useState({})
  const [scenarioId, setScenarioId] = useState('normal')
  const [thresholds, setThresholds] = useState(DEMO_THRESHOLDS)
  const [mode, setMode] = useState('outer')
  const [layer, setLayer] = useState('full')
  const [labels, setLabels] = useState(true)
  const [scan, setScan] = useState(true)
  const [modelStatus, setModelStatus] = useState('loading')
  const [updatedAt, setUpdatedAt] = useState(() => new Date())
  const [mobileDetailsOpen, setMobileDetailsOpen] = useState(false)
  const [isMobileViewport, setIsMobileViewport] = useState(() => (
    typeof window !== 'undefined' && window.matchMedia?.('(max-width: 690px)').matches === true
  ))
  const [activeMetric, setActiveMetric] = useState(0)
  const [astronaut, setAstronaut] = useState('A-01')
  const [syntheticAstronauts, setSyntheticAstronauts] = useState([])
  const [liveDashboard, setLiveDashboard] = useState(null)
  const [liveStatus, setLiveStatus] = useState('idle')
  const [liveError, setLiveError] = useState('')
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [liveRefreshVersion, setLiveRefreshVersion] = useState(0)
  const [modelRetryKey, setModelRetryKey] = useState(0)
  const [assistant, setAssistant] = useState(null)
  const [assistantStatus, setAssistantStatus] = useState('NOT REQUESTED')
  const controlsRef = useRef()
  const mobileDetailsTriggerRef = useRef(null)
  const analysisRequestRef = useRef({ controller: null, generation: 0 })
  const reducedMotion = usePrefersReducedMotion()
  const snapshot = useMemo(() => createDemoSnapshot(scenarioId), [scenarioId])
  const demoEvaluation = useMemo(
    () => evaluateSyntheticAlerts(snapshot.readings, {
      thresholds,
      regionAlerts: snapshot.regionAlerts,
    }),
    [snapshot, thresholds],
  )
  const emptyReadings = {
    heart_rate_bpm: null,
    spo2_percent: null,
    body_temperature_c: null,
    respiration_rate_bpm: null,
  }
  const liveReadings = liveDashboard
    ? {
      heart_rate_bpm: liveDashboard.readings.heart_rate_bpm,
      spo2_percent: liveDashboard.readings.spo2_percent,
      body_temperature_c: liveDashboard.readings.skin_temperature_c,
      respiration_rate_bpm: liveDashboard.readings.respiration_rate_bpm,
    }
    : emptyReadings
  const liveAnalysis = liveDashboard?.analysis ?? null
  const liveAlerts = getAnalysisFindings(liveAnalysis)
  const isLive = appMode === 'live'
  const readings = isLive ? liveReadings : snapshot.readings
  const alerts = isLive ? liveAlerts : demoEvaluation.alerts
  const regionStatuses = isLive
    ? Object.fromEntries(Object.keys(demoEvaluation.regionStatuses).map((region) => [region, 'no-data']))
    : demoEvaluation.regionStatuses
  const history = useMemo(
    () => isLive ? liveDashboard?.history ?? [] : getDemoHistory(snapshot.readings),
    [isLive, liveDashboard, snapshot],
  )
  const metrics = useMemo(() => getMetrics(readings, alerts, isLive), [readings, alerts, isLive])
  const focusPoints = modelInfo.focusPoints ?? {}

  const cancelPendingAnalysis = useCallback(() => {
    analysisRequestRef.current.generation += 1
    analysisRequestRef.current.controller?.abort()
    analysisRequestRef.current.controller = null
  }, [])

  const requestAssistant = useCallback(async (analysis, { signal } = {}) => {
    if (!analysis || !astronaut || appMode !== 'live') return
    const configuredMode = import.meta.env.VITE_ASSISTANT_MODE === 'local' ? 'local' : 'mock'
    setAssistantStatus(configuredMode === 'local' ? 'CONNECTING' : 'MOCK MODE')
    try {
      const response = await askForExplanation(astronaut, analysis.id, configuredMode, { signal })
      setAssistant(response)
      setAssistantStatus(response.is_mock ? 'MOCK RESPONSE' : 'CONNECTED RESPONSE')
    } catch (error) {
      if (isApiRequestCancelled(error)) return
      if (configuredMode === 'local') {
        try {
          const fallback = await askForExplanation(astronaut, analysis.id, 'mock', { signal })
          setAssistant(fallback)
          setAssistantStatus('MOCK FALLBACK')
          return
        } catch (fallbackError) {
          if (isApiRequestCancelled(fallbackError)) return
          setAssistant(null)
          setAssistantStatus(`UNAVAILABLE · ${fallbackError.message}`)
          return
        }
      }
      setAssistant(null)
      setAssistantStatus(`UNAVAILABLE · ${error.message}`)
    }
  }, [appMode, astronaut])

  useEffect(() => {
    if (!isLive) return undefined
    let active = true
    const controller = new AbortController()
    fetchSyntheticAstronauts({ signal: controller.signal })
      .then((profiles) => {
        if (!active) return
        setSyntheticAstronauts(profiles)
        if (!profiles.length) {
          setAstronaut('')
          setLiveStatus('empty')
          return
        }
        setAstronaut((current) => profiles.some((profile) => profile.astronaut_id === current)
          ? current
          : profiles[0].astronaut_id)
      })
      .catch((error) => {
        if (!active || isApiRequestCancelled(error)) return
        setSyntheticAstronauts([])
        setLiveStatus('error')
        setLiveError(error.message)
      })
    return () => {
      active = false
      controller.abort()
    }
  }, [isLive, liveRefreshVersion])

  useEffect(() => {
    if (!isLive || !astronaut || !syntheticAstronauts.some((profile) => profile.astronaut_id === astronaut)) return undefined
    let active = true
    const controller = new AbortController()
    fetchLiveDashboard(astronaut, { signal: controller.signal })
      .then((dashboard) => {
        if (!active) return
        setLiveDashboard(dashboard)
        setLiveStatus(dashboard.source ? 'ready' : 'empty')
        setUpdatedAt(new Date())
        if (dashboard.analysis) requestAssistant(dashboard.analysis, { signal: controller.signal })
      })
      .catch((error) => {
        if (!active || isApiRequestCancelled(error)) return
        setLiveStatus('error')
        setLiveError(error.message)
      })
    return () => {
      active = false
      controller.abort()
    }
  }, [isLive, astronaut, syntheticAstronauts, requestAssistant, liveRefreshVersion])

  useEffect(() => {
    if (!window.matchMedia) return undefined
    const mediaQuery = window.matchMedia('(max-width: 690px)')
    const updateViewport = (event) => setIsMobileViewport(event.matches)
    mediaQuery.addEventListener?.('change', updateViewport)
    return () => mediaQuery.removeEventListener?.('change', updateViewport)
  }, [])

  useEffect(() => () => cancelPendingAnalysis(), [cancelPendingAnalysis])

  const resetCamera = () => {
    setSelectedRegion(null)
    controlsRef.current?.reset()
  }

  const selectRegion = (region) => {
    setSelectedRegion(region && focusPoints[region] ? region : null)
    if (isMobileViewport && mobileDetailsOpen) setMobileDetailsOpen(false)
  }

  const updateThreshold = (key, direction, level, inputValue) => {
    const value = Number(inputValue)
    if (!Number.isFinite(value) || value < 1) return

    const previous = thresholds[key][direction]
    const next = {
      ...previous,
      [level]: value,
    }
    if (level === 'warning') next.critical = Math.max(next.critical, value)
    if (level === 'critical') next.warning = Math.min(next.warning, value)

    setThresholds({
      ...thresholds,
      [key]: {
        ...thresholds[key],
        [direction]: next,
      },
    })
    setUpdatedAt(new Date())
  }

  const changeScenario = (nextScenarioId) => {
    setScenarioId(nextScenarioId)
    setSelectedRegion(null)
    setUpdatedAt(new Date())
  }

  const zoomCamera = (scale) => {
    const controls = controlsRef.current
    if (!controls) return
    const offset = controls.object.position.clone().sub(controls.target)
    const nextDistance = THREE.MathUtils.clamp(
      offset.length() * scale,
      controls.minDistance,
      controls.maxDistance,
    )
    offset.setLength(nextDistance)
    controls.object.position.copy(controls.target).add(offset)
    controls.update()
  }

  const changeAppMode = (nextMode) => {
    if (nextMode === appMode) return
    cancelPendingAnalysis()
    setAnalysisLoading(false)
    setAppMode(nextMode)
    setSelectedRegion(null)
    setAssistant(null)
    setLiveDashboard(null)
    setLiveError('')
    if (nextMode === 'demo') setAstronaut('A-01')
    else {
      setLiveStatus('loading')
      setAstronaut('')
      setSyntheticAstronauts([])
    }
  }

  const changeAstronaut = (nextAstronaut) => {
    cancelPendingAnalysis()
    setAnalysisLoading(false)
    setAstronaut(nextAstronaut)
    if (isLive) {
      setLiveStatus('loading')
      setLiveError('')
      setLiveDashboard(null)
      setAssistant(null)
    }
  }

  const retryLiveConnection = () => {
    if (!isLive) return
    setLiveStatus('loading')
    setLiveError('')
    setLiveDashboard(null)
    setSyntheticAstronauts([])
    setAstronaut('')
    setLiveRefreshVersion((version) => version + 1)
  }

  const closeMobileDetails = useCallback(() => setMobileDetailsOpen(false), [])

  const handleRunAnalysis = async () => {
    if (!astronaut || !liveDashboard?.source) return
    cancelPendingAnalysis()
    const controller = new AbortController()
    const generation = analysisRequestRef.current.generation
    analysisRequestRef.current.controller = controller
    setAnalysisLoading(true)
    setLiveError('')
    setAssistant(null)
    try {
      const analysis = await runLocalAnalysis(astronaut, liveDashboard.source, {
        signal: controller.signal,
      })
      if (controller.signal.aborted || analysisRequestRef.current.generation !== generation) return
      setLiveDashboard((current) => current ? { ...current, analysis } : current)
      setUpdatedAt(new Date())
      await requestAssistant(analysis, { signal: controller.signal })
    } catch (error) {
      if (!isApiRequestCancelled(error)
        && analysisRequestRef.current.generation === generation) setLiveError(error.message)
    } finally {
      if (analysisRequestRef.current.generation === generation) {
        analysisRequestRef.current.controller = null
        setAnalysisLoading(false)
      }
    }
  }

  return (
    <main className="command-center">
      <div className="ambient-glow ambient-left" />
      <div className="ambient-glow ambient-right" />
      <Header
        astronaut={astronaut}
        setAstronaut={changeAstronaut}
        hasAlerts={alerts.length > 0}
        live={isLive}
        astronauts={syntheticAstronauts}
        analysis={liveAnalysis}
      />
      <div className="command-content">
        <LeftHud
          astronaut={astronaut}
          activeMetric={activeMetric}
          setActiveMetric={setActiveMetric}
          metrics={metrics}
          history={history}
          scenarioId={scenarioId}
          onScenarioChange={changeScenario}
          thresholds={thresholds}
          onThresholdChange={updateThreshold}
          live={isLive}
          onModeChange={changeAppMode}
          liveStatus={liveStatus}
          liveError={liveError}
          liveTimestamp={liveDashboard?.timestamp}
          onRetryLive={retryLiveConnection}
          onRunAnalysis={handleRunAnalysis}
          analysisLoading={analysisLoading}
        />
        <section className="hologram-stage" aria-label="Interactive 3D astronaut digital twin">
          <button
            type="button"
            ref={mobileDetailsTriggerRef}
            className="mobile-details-toggle"
            onClick={() => setMobileDetailsOpen((open) => !open)}
            aria-expanded={mobileDetailsOpen}
            aria-controls="region-details-panel"
            aria-label={mobileDetailsOpen ? 'Close region details' : 'Open region details'}
          >
            {mobileDetailsOpen ? 'CLOSE DETAILS' : 'REGION DETAILS'}
          </button>
          <div className="stage-header">
            <span><i /> ANATOMY VIEW <b>/</b> SYNTHETIC EDUCATIONAL DEMO</span>
            {labels && selectedRegion && (
              <span className="stage-focus-label">FOCUS / {REGIONS[selectedRegion].shortName}</span>
            )}
            <span className="stage-coordinates">LAYER / {layer.toUpperCase()}</span>
          </div>
          <div className="stage-corner corner-tl" />
          <div className="stage-corner corner-tr" />
          <div className="stage-corner corner-bl" />
          <div className="stage-corner corner-br" />
          <div className="stage-grid" />
          <div className="scanline-overlay" />
          <div className="vertical-guide" />
          <div className="scene-wrap">
            <DigitalHuman
              mode={mode}
              layer={layer}
              selected={selectedRegion}
              scan={scan}
              regionStatuses={regionStatuses}
              controlsRef={controlsRef}
              focusPoints={focusPoints}
              onSelect={selectRegion}
              onModelStatusChange={setModelStatus}
              onModelInfo={setModelInfo}
              retryModelKey={modelRetryKey}
              reducedMotion={reducedMotion}
            />
          </div>
          <div className="stage-footer">
            <span><i /> {modelStatus === 'ready' ? 'ANATOMY GLB' : 'SCHEMATIC ONLY'}</span>
            <span>{selectedRegion ? REGIONS[selectedRegion].code : 'FULL BODY VIEW'}</span>
            <span>REGION DATA <b>NOT LOCALIZED</b></span>
            <a
              className="model-attribution"
              href="https://github.com/MervinR07/open-anatomy-3d"
              target="_blank"
              rel="noreferrer"
            >
              BODYPARTS3D · OPEN-ANATOMY · CC BY 4.0
            </a>
          </div>
          <ViewControls
            mode={mode}
            layer={layer}
            setLayer={setLayer}
            setMode={setMode}
            labels={labels}
            setLabels={setLabels}
            scan={scan}
            setScan={setScan}
            resetCamera={resetCamera}
            zoomCamera={zoomCamera}
            selected={selectedRegion}
            focusPoints={focusPoints}
            onSelectRegion={selectRegion}
          />
          <div className={`model-note model-status-${modelStatus}`} role="status" aria-live="polite">
            {modelStatus === 'ready' ? <Check size={11} /> : <AlertTriangle size={11} />}
            {modelStatus === 'ready'
              ? 'ANATOMY GLB LOADED · SELECT A NAMED REGION'
              : modelStatus === 'loading'
                ? 'LOADING MODEL · NON-ANATOMICAL SCHEMATIC SHOWN'
                : modelStatus === 'error'
                  ? 'MODEL LOAD FAILED · NON-ANATOMICAL SCHEMATIC SHOWN'
                  : 'MODEL FILE MISSING · NON-ANATOMICAL SCHEMATIC SHOWN'}
          </div>
          {(modelStatus === 'error' || modelStatus === 'missing') && (
            <button type="button" className="model-retry-floating" onClick={() => setModelRetryKey((key) => key + 1)}>
              RETRY MODEL LOAD
            </button>
          )}
        </section>
        {isMobileViewport && mobileDetailsOpen && (
          <button
            type="button"
            className="mobile-drawer-backdrop"
            aria-label="Close region details"
            onClick={closeMobileDetails}
          />
        )}
        <RightHud
          selected={selectedRegion}
          readings={readings}
          alerts={alerts}
          regionStatuses={regionStatuses}
          onSelectRegion={selectRegion}
          updatedAt={updatedAt}
          mobileOpen={mobileDetailsOpen}
          onClose={closeMobileDetails}
          mobileView={isMobileViewport}
          triggerRef={mobileDetailsTriggerRef}
          live={isLive}
          analysis={liveAnalysis}
          assistant={assistant}
          assistantStatus={assistantStatus}
        />
      </div>
      <footer className="bottom-status">
        <div className="footer-left"><span className="footer-shield"><Shield size={13} /></span><span><b>AEGIS PROTOTYPE</b> <i>·</i> SYNTHETIC EDUCATIONAL PROTOTYPE</span></div>
        <div className="footer-center">
          <span>MODE</span><b>{isLive ? 'LIVE API' : 'DEMO'}</b>
          <span className="footer-divider" />
          <span>DATA SOURCE</span><b>SYNTHETIC</b>
          <span className="footer-divider" />
          <span>ANALYSIS</span><b>{isLive ? getAnalysisStatusLabel(liveAnalysis) : 'THRESHOLD DEMO'}</b>
        </div>
        <div className="footer-right"><span>PROTOTYPE</span><span className="footer-divider" /><span>NASA SPACE APPS 2026</span></div>
      </footer>
    </main>
  )
}

export default App
