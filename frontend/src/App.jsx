import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Sparkles } from '@react-three/drei'
import * as THREE from 'three'
import AnatomyModel from './AnatomyModel.jsx'
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  AudioLines,
  BrainCircuit,
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

const REGIONS = {
  head: {
    name: 'Neural / cranial',
    shortName: 'HEAD',
    code: 'CRN-01',
    description: 'Neural activity and cranial sensor channels',
    position: [0, 1.55, 0.26],
    metrics: [
      ['Neural activity', 'Stable', 'Within personal baseline'],
      ['Motion artifact', '0.03 g', 'Low signal interference'],
      ['Sensor contact', '98.4%', 'Nominal contact quality'],
    ],
    explanation:
      'Cranial channels are tracking within the synthetic personal baseline. No model flag is active for this region.',
  },
  heart: {
    name: 'Cardiovascular',
    shortName: 'HEART',
    code: 'CV-02',
    description: 'Cardiac rhythm and circulation indicators',
    position: [0.12, 0.48, 0.48],
    metrics: [
      ['Heart rate', '72 bpm', '−2 bpm from baseline'],
      ['Rhythm signal', 'Regular', 'No synthetic flag'],
      ['Perfusion index', '4.8%', 'Within baseline range'],
    ],
    explanation:
      'Heart-rate trend is near the synthetic crew baseline. This is a prototype reading, not a medical assessment.',
  },
  lungs: {
    name: 'Respiratory',
    shortName: 'LUNGS',
    code: 'RESP-03',
    description: 'Respiration and oxygenation sensor channels',
    position: [0, 0.72, 0.46],
    metrics: [
      ['SpO₂', '98%', '+1% from baseline'],
      ['Respiration', '16 /min', 'Within baseline range'],
      ['Cabin CO₂', '500 ppm', 'Synthetic environment feed'],
    ],
    explanation:
      'Respiration and oxygenation channels are stable in this generated scenario. Cabin CO₂ is environment telemetry, not a personal clinical measurement.',
  },
  abdomen: {
    name: 'Core / abdomen',
    shortName: 'CORE',
    code: 'CORE-04',
    description: 'Core temperature and abdominal sensor channels',
    position: [0, -0.15, 0.43],
    metrics: [
      ['Skin temperature', '36.8 °C', 'Within baseline range'],
      ['Core trend', 'Stable', 'No synthetic flag'],
      ['Sensor contact', '97.1%', 'Nominal contact quality'],
    ],
    explanation:
      'Core-region channels show no deviation in this synthetic snapshot. Sensor contact remains nominal.',
  },
}

const METRICS = [
  {
    name: 'Heart rate',
    value: 72,
    unit: 'bpm',
    baseline: '74 bpm',
    change: '−2',
    icon: Heart,
    color: '#ff7892',
    historyKey: 'heart',
  },
  {
    name: 'Oxygen saturation',
    value: 98,
    unit: '%',
    baseline: '97%',
    change: '+1',
    icon: Activity,
    color: '#71e7ff',
    historyKey: 'oxygen',
  },
  {
    name: 'Body temperature',
    value: 36.8,
    unit: '°C',
    baseline: '36.7 °C',
    change: '+0.1',
    icon: Moon,
    color: '#ffbc77',
    historyKey: 'temperature',
  },
  {
    name: 'Respiration',
    value: 16,
    unit: '/min',
    baseline: '16 /min',
    change: '0',
    icon: Wind,
    color: '#8fa9ff',
    historyKey: 'respiration',
  },
]

const HISTORY = Array.from({ length: 28 }, (_, index) => {
  const wave = (offset, magnitude, frequency) =>
    offset + Math.sin(index * frequency) * magnitude + Math.cos(index * 0.37) * magnitude * 0.28

  return {
    time: `${String(Math.floor(index / 2)).padStart(2, '0')}:${index % 2 ? '30' : '00'}`,
    heart: wave(72, 4.3, 0.75),
    oxygen: wave(97.8, 0.9, 0.53),
    temperature: wave(36.8, 0.16, 0.3),
    respiration: wave(16, 1.6, 0.9),
  }
})

function ProjectionPlatform() {
  const rings = useRef([])
  useFrame(({ clock }) => {
    rings.current.forEach((ring, index) => {
      if (ring) ring.rotation.z = clock.elapsedTime * (index % 2 ? -0.08 : 0.08)
    })
  })

  return (
    <group position={[0, -2.02, 0]}>
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
          opacity={0.12}
          side={2}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      <mesh position={[0, 0, 0.01]}>
        <planeGeometry args={[3.5, 0.008]} />
        <meshBasicMaterial color="#c0fbff" transparent opacity={0.62} side={2} />
      </mesh>
    </group>
  )
}

function CameraFocus({ controlsRef, selected }) {
  const target = useRef(new THREE.Vector3(0, 0, 0))
  const focusPoints = {
    head: [0, 1.4, 0],
    heart: [0, 0.55, 0],
    lungs: [0, 0.72, 0],
    abdomen: [0, -0.18, 0],
  }

  useFrame((_, delta) => {
    const controls = controlsRef.current
    if (!controls) return
    const next = new THREE.Vector3(...(focusPoints[selected] ?? [0, 0, 0]))
    target.current.lerp(next, 1 - Math.exp(-delta * 2.8))
    controls.target.copy(target.current)
    controls.update()
  })
  return null
}

function DigitalHuman({ mode, selected, labels, scan, controlsRef, onSelect, onModelStatusChange }) {
  return (
    <Canvas
      camera={{ position: [0, 0.02, 5.8], fov: 40, near: 0.1, far: 100 }}
      dpr={[1, 1.6]}
      gl={{ antialias: true, alpha: true }}
      onPointerMissed={() => onSelect(null)}
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
      <Sparkles count={110} scale={[4.5, 5.2, 3.5]} size={2.2} speed={0.18} opacity={0.58} color="#85eaff" />
      <AnatomyModel
        mode={mode}
        selected={selected}
        labels={labels}
        onSelect={onSelect}
        onStatusChange={onModelStatusChange}
      />
      <ProjectionPlatform />
      <ScanBeam active={scan} />
      <CameraFocus controlsRef={controlsRef} selected={selected} />
      <OrbitControls
        ref={controlsRef}
        makeDefault
        enablePan={false}
        enableDamping
        dampingFactor={0.08}
        minDistance={4.2}
        maxDistance={11}
        minPolarAngle={Math.PI * 0.29}
        maxPolarAngle={Math.PI * 0.68}
        rotateSpeed={0.65}
      />
    </Canvas>
  )
}

function MetricCard({ metric, index, active, onSelect }) {
  const Icon = metric.icon
  const positive = metric.change.startsWith('+')

  return (
    <button
      className={`metric-readout ${active ? 'metric-active' : ''}`}
      onClick={onSelect}
      style={{ '--metric-color': metric.color, '--stagger': `${index * 70}ms` }}
    >
      <div className="metric-topline">
        <span className="metric-icon"><Icon size={14} strokeWidth={1.7} /></span>
        <span className="metric-name">{metric.name}</span>
        <span className="metric-live"><i />LIVE</span>
      </div>
      <div className="metric-number">
        <strong>{metric.value}</strong>
        <span>{metric.unit}</span>
      </div>
      <div className="metric-baseline">
        <span>BASE {metric.baseline}</span>
        <span className={positive ? 'trend-up' : 'trend-down'}>
          {positive ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
          {metric.change}
        </span>
      </div>
    </button>
  )
}

function EcgChart({ metric }) {
  return (
    <div className="chart-frame">
      <div className="chart-heading">
        <div>
          <span className="eyebrow">LIVE TELEMETRY</span>
          <strong><Activity size={13} /> {metric.name.toUpperCase()}</strong>
        </div>
        <span className="chart-window">LAST 14H</span>
      </div>
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={HISTORY} margin={{ top: 8, right: 2, left: -26, bottom: 0 }}>
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
        </ResponsiveContainer>
      </div>
      <div className="chart-footnote">
        <span>PERSONAL BASELINE</span>
        <span className="baseline-key" />
        <span>SIMULATED SIGNAL</span>
      </div>
    </div>
  )
}

function Header({ astronaut, setAstronaut, missionTime }) {
  return (
    <header className="topbar">
      <div className="brand-lockup">
        <div className="adora-mark"><span /><span /><span /></div>
        <div className="brand-name">ADORA<span> / AEGIS</span></div>
        <div className="brand-divider" />
        <div className="vital-brand">powered by <b>VitalTwin</b></div>
      </div>
      <div className="mission-lockup">
        <span className="eyebrow">MISSION CONTROL <b>/</b> LEO-07</span>
        <strong>ORBITAL VITALS MONITOR</strong>
      </div>
      <div className="topbar-right">
        <label className="select-wrap">
          <span>CREW</span>
          <select value={astronaut} onChange={(event) => setAstronaut(event.target.value)} aria-label="Select synthetic astronaut">
            <option value="A-01">ASTRONAUT A-01</option>
            <option value="A-02">ASTRONAUT A-02</option>
            <option value="A-03">ASTRONAUT A-03</option>
          </select>
          <ChevronDown size={12} />
        </label>
        <div className="elapsed-time">
          <span>MISSION ELAPSED <i>SIMULATED</i></span>
          <strong>{missionTime}</strong>
        </div>
        <div className="system-state"><i /><span>ALL SYSTEMS<br /><b>NOMINAL</b></span></div>
        <div className="synthetic-tag"><span /> SIMULATION <b>/</b> SYNTHETIC DATA</div>
      </div>
    </header>
  )
}

function LeftHud({ astronaut, onSelect, activeMetric, setActiveMetric }) {
  const active = METRICS[activeMetric]
  return (
    <aside className="left-hud">
      <div className="panel-title">
        <div><span className="panel-index">01</span><span>CREW VITALS</span></div>
        <span className="feed-state"><i /> FEED ACTIVE</span>
      </div>
      <div className="crew-profile">
        <div className="crew-avatar">A<span>{astronaut.slice(-2)}</span></div>
        <div className="crew-details">
          <strong>CREW MEMBER {astronaut}</strong>
          <span>EXPEDITION SPECIALIST</span>
        </div>
        <div className="crew-signal"><Signal size={15} /></div>
      </div>
      <div className="metrics-stack">
        {METRICS.map((metric, index) => (
          <MetricCard
            key={metric.name}
            metric={metric}
            index={index}
            active={activeMetric === index}
            onSelect={() => {
              setActiveMetric(index)
              if (metric.name === 'Heart rate') onSelect('heart')
              if (metric.name === 'Oxygen saturation' || metric.name === 'Respiration') onSelect('lungs')
              if (metric.name === 'Body temperature') onSelect('abdomen')
            }}
          />
        ))}
      </div>
      <EcgChart metric={active} />
      <div className="baseline-note">
        <span className="baseline-symbol"><Crosshair size={13} /></span>
        <span>Values compared to <b>individual baseline</b><br />Synthetic crew profile · 14h window</span>
        <CircleHelp size={13} className="help-icon" />
      </div>
    </aside>
  )
}

function RightHud({ selected }) {
  const region = selected ? REGIONS[selected] : null
  return (
    <aside className="right-hud">
      <div className="panel-title">
        <div><span className="panel-index">02</span><span>REGION ANALYSIS</span></div>
        <Maximize2 size={13} className="muted-icon" />
      </div>
      <div className="region-overview">
        <div className={`region-orb ${selected ? `orb-${selected}` : ''}`}>
          <span className="orb-ring" />
          <span className="orb-core"><Activity size={21} /></span>
        </div>
        <div>
          <span className="eyebrow">{region?.code ?? 'FULL BODY SCAN'}</span>
          <h2>{region?.name ?? 'System overview'}</h2>
          <p>{region?.description ?? 'Select a highlighted body region to inspect its sensor channels.'}</p>
        </div>
      </div>
      <div className="section-rule"><span>REGIONAL INDICATORS</span><i /></div>
      <div className="regional-metrics">
        {(region?.metrics ?? [
          ['Sensor channels', '12 / 12', 'All synthetic feeds online'],
          ['Data integrity', '99.2%', 'Signal quality nominal'],
          ['Baseline variance', 'Low', 'No active deviation'],
        ]).map(([label, value, note]) => (
          <div className="regional-metric" key={label}>
            <div className="regional-label">{label}<span className="metric-check"><Check size={10} /></span></div>
            <strong>{value}</strong>
            <span className="regional-note">{note}</span>
          </div>
        ))}
      </div>
      <div className="ml-status">
        <div className="ml-icon"><BrainCircuit size={17} /></div>
        <div className="ml-copy">
          <span className="eyebrow">ML ANOMALY SCREEN</span>
          <strong><i /> NO ANOMALY FLAGGED</strong>
        </div>
        <span className="ml-score">0.04</span>
      </div>
      <div className="assistant-panel">
        <div className="assistant-heading">
          <span className="assistant-spark"><SparklesIcon size={13} /></span>
          <div><span className="eyebrow">AEGIS ASSISTANT</span><b>Signal interpretation</b></div>
          <span className="assistant-beta">BETA</span>
        </div>
        <p>{region?.explanation ?? 'All monitored channels remain within the synthetic personal baseline in this example snapshot. Select a region for a focused, non-clinical summary.'}</p>
        <span className="assistant-disclaimer"><Shield size={11} /> PROTOTYPE INTERPRETATION · NOT MEDICAL ADVICE</span>
      </div>
      <div className="alerts-heading">
        <span>RECENT EVENTS</span><span>02</span>
      </div>
      <div className="alert-item">
        <span className="alert-mark"><Check size={11} /></span>
        <div><b>Sensor sync complete</b><span>All channels · 00:14 ago</span></div>
        <span className="alert-type">INFO</span>
      </div>
      <div className="alert-item">
        <span className="alert-mark alert-mark-blue"><AudioLines size={11} /></span>
        <div><b>Baseline refreshed</b><span>Crew profile · 02:31 ago</span></div>
        <span className="alert-type">SYNC</span>
      </div>
    </aside>
  )
}

function ViewControls({
  mode,
  setMode,
  labels,
  setLabels,
  scan,
  setScan,
  resetCamera,
  zoomCamera,
}) {
  return (
    <div className="view-controls">
      <div className="view-control-label"><span>HOLOGRAM VIEW</span><i /></div>
      <div className="control-group camera-controls">
        <button onClick={resetCamera} title="Reset camera" aria-label="Reset camera"><RotateCcw size={14} /><span>RESET</span></button>
        <i />
        <button onClick={() => zoomCamera(0.82)} title="Zoom in" aria-label="Zoom in"><Plus size={15} /></button>
        <button onClick={() => zoomCamera(1.22)} title="Zoom out" aria-label="Zoom out"><Minus size={15} /></button>
      </div>
      <div className="control-group mode-controls" role="group" aria-label="Body display mode">
        {[
          ['outer', 'OUTER'],
          ['wireframe', 'WIRE'],
          ['anatomy', 'ANATOMY'],
        ].map(([value, label]) => (
          <button
            key={value}
            className={mode === value ? 'control-active' : ''}
            onClick={() => setMode(value)}
          >
            {value === 'wireframe' ? <Move3D size={13} /> : value === 'anatomy' ? <Activity size={13} /> : <ScanLine size={13} />}
            {label}
          </button>
        ))}
      </div>
      <div className="control-group toggles">
        <button className={labels ? 'toggle-on' : ''} onClick={() => setLabels(!labels)} title="Toggle labels">
          <span className="toggle-switch"><i /></span><span>LABELS</span>
        </button>
        <button className={scan ? 'toggle-on' : ''} onClick={() => setScan(!scan)} title="Toggle scan effect">
          <span className="toggle-switch"><i /></span><span>SCAN</span>
        </button>
      </div>
      <div className="drag-hint"><Move3D size={13} /><span>DRAG TO ROTATE</span></div>
    </div>
  )
}

function App() {
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [mode, setMode] = useState('outer')
  const [labels, setLabels] = useState(true)
  const [scan, setScan] = useState(true)
  const [modelStatus, setModelStatus] = useState('loading')
  const [activeMetric, setActiveMetric] = useState(0)
  const [astronaut, setAstronaut] = useState('A-01')
  const [missionSeconds, setMissionSeconds] = useState(2 * 3600 + 14 * 60 + 8)
  const controlsRef = useRef()

  useEffect(() => {
    const timer = window.setInterval(() => setMissionSeconds((time) => time + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])

  const missionTime = useMemo(() => {
    const hours = Math.floor(missionSeconds / 3600)
    const minutes = Math.floor((missionSeconds % 3600) / 60)
    const seconds = missionSeconds % 60
    return `T+${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }, [missionSeconds])

  const resetCamera = () => {
    setSelectedRegion(null)
    controlsRef.current?.reset()
  }

  const zoomCamera = (scale) => {
    const controls = controlsRef.current
    if (!controls) return
    const offset = controls.object.position.clone().sub(controls.target).multiplyScalar(scale)
    controls.object.position.copy(controls.target).add(offset)
    controls.update()
  }

  return (
    <main className="command-center">
      <div className="ambient-glow ambient-left" />
      <div className="ambient-glow ambient-right" />
      <Header astronaut={astronaut} setAstronaut={setAstronaut} missionTime={missionTime} />
      <div className="command-content">
        <LeftHud
          astronaut={astronaut}
          onSelect={setSelectedRegion}
          activeMetric={activeMetric}
          setActiveMetric={setActiveMetric}
        />
        <section className="hologram-stage" aria-label="Interactive 3D astronaut digital twin">
          <div className="stage-header">
            <span><i /> DIGITAL TWIN <b>/</b> {modelStatus === 'ready' ? 'ANATOMY MODEL' : 'MODEL ASSET PENDING'}</span>
            <span className="stage-coordinates">X 00.00 <b>Y</b> 01.84 <b>Z</b> 00.00</span>
          </div>
          <div className="stage-corner corner-tl" />
          <div className="stage-corner corner-tr" />
          <div className="stage-corner corner-bl" />
          <div className="stage-corner corner-br" />
          <div className="stage-grid" />
          <div className="scanline-overlay" />
          <div className="vertical-guide" />
          <div className="stage-readout stage-readout-left">
            <span>PROJECTION MATRIX</span><b>ACTIVE</b>
            <i /><span>DEPTH MAPPING</span><b>12.8 CM</b>
          </div>
          <div className="stage-readout stage-readout-right">
            <span>MODEL STATUS</span><b>{modelStatus === 'ready' ? 'GLB ONLINE' : modelStatus === 'error' ? 'LOAD ERROR' : modelStatus === 'missing' ? 'ASSET MISSING' : 'LOADING'}</b>
            <i /><span>LAST SYNC</span><b>00:00:14</b>
          </div>
          <div className="scene-wrap">
            <DigitalHuman
              mode={mode}
              selected={selectedRegion}
              labels={labels}
              scan={scan}
              controlsRef={controlsRef}
              onSelect={setSelectedRegion}
              onModelStatusChange={setModelStatus}
            />
          </div>
          <div className="stage-footer">
            <span><i /> {modelStatus === 'ready' ? 'ANATOMY GLB' : 'HOLOGRAM FALLBACK'}</span>
            <span>{selectedRegion ? REGIONS[selectedRegion].code : 'FULL BODY VIEW'}</span>
            <span>WEBGL <b>●</b></span>
          </div>
          <ViewControls
            mode={mode}
            setMode={setMode}
            labels={labels}
            setLabels={setLabels}
            scan={scan}
            setScan={setScan}
            resetCamera={resetCamera}
            zoomCamera={zoomCamera}
          />
          <div className={`model-note model-status-${modelStatus}`}>
            {modelStatus === 'ready' ? <Check size={11} /> : <AlertTriangle size={11} />}
            {modelStatus === 'ready'
              ? 'ANATOMY GLB LOADED · SELECT HOTSPOTS OR NAMED MESHES'
              : modelStatus === 'loading'
                ? 'CHECKING ANATOMY MODEL · NON-ANATOMICAL CONTOUR SHOWN'
                : modelStatus === 'error'
                  ? 'MODEL LOAD FAILED · CHECK GLB FILE AND MESH NAMES'
                  : 'MODEL NOT INSTALLED · ADD /MODELS/ASTRONAUT-ANATOMY.GLB'}
          </div>
        </section>
        <RightHud selected={selectedRegion} />
      </div>
      <footer className="bottom-status">
        <div className="footer-left"><span className="footer-shield"><Shield size={13} /></span><span><b>AEGIS PROTOTYPE</b> <i>·</i> FLIGHT HEALTH SYSTEMS</span></div>
        <div className="footer-center"><span>DATA LINK</span><b><i /> SIMULATED</b><span className="footer-divider" /><span>UPLINK LATENCY</span><b>42 MS</b><span className="footer-divider" /><span>DATA SOURCE</span><b>GENERATED FEED</b></div>
        <div className="footer-right"><span>V 0.1.0</span><span className="footer-divider" /><span>NASA SPACE APPS 2026</span></div>
      </footer>
    </main>
  )
}

export default App
