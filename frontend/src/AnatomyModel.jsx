import { useEffect, useMemo, useRef, useState } from 'react'
import { Html } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

const MODEL_PATH = '/models/astronaut-anatomy.glb'
const REGION_ORDER = ['head', 'heart', 'lungs', 'abdomen']
const HOTSPOTS = {
  head: [0, 1.4, 0.3],
  heart: [0.1, 0.48, 0.42],
  lungs: [0, 0.78, 0.4],
  abdomen: [0, -0.22, 0.38],
}
const REGION_LABELS = {
  head: 'HEAD',
  heart: 'HEART',
  lungs: 'LUNGS',
  abdomen: 'CORE',
}
const REGION_NAMES = {
  head: /head|brain|cranial|skull/i,
  heart: /heart|cardiac/i,
  lungs: /lung|pulmonary/i,
  abdomen: /abdomen|abdominal|stomach|core/i,
}

function getRegion(object) {
  for (let current = object; current; current = current.parent) {
    if (REGION_ORDER.includes(current.userData.region)) return current.userData.region
    const match = REGION_ORDER.find((region) => REGION_NAMES[region].test(current.name))
    if (match) return match
  }
  return null
}

function setModelMaterials(root, mode, selected) {
  root.traverse((object) => {
    if (!object.isMesh) return
    const region = getRegion(object)
    const materials = Array.isArray(object.material) ? object.material : [object.material]

    materials.forEach((material) => {
      if (!material.userData.aegisOriginal) {
        material.userData.aegisOriginal = {
          color: material.color?.clone(),
          emissive: material.emissive?.clone(),
          opacity: material.opacity,
          transparent: material.transparent,
          depthWrite: material.depthWrite,
        }
      }

      const original = material.userData.aegisOriginal
      if (mode === 'anatomy') {
        if (original.color) material.color.copy(original.color)
        if (original.emissive) material.emissive.copy(original.emissive)
        material.opacity = 0.96
        material.transparent = original.transparent
        material.depthWrite = original.depthWrite
        material.wireframe = false
      } else {
        material.color.set(mode === 'wireframe' ? '#9af5ff' : '#59cde7')
        if (material.emissive) material.emissive.set(mode === 'wireframe' ? '#39b9d4' : '#12677d')
        material.opacity = mode === 'wireframe' ? 0.84 : 0.52
        material.transparent = true
        material.depthWrite = false
        material.wireframe = mode === 'wireframe'
      }

      if (material.emissive) {
        material.emissiveIntensity = region === selected ? 1.8 : 0.8
        if (region === selected) material.emissive.set('#45d9ff')
      }
      material.needsUpdate = true
    })
  })
}

function createTaperedTube(points, radii) {
  const curve = new THREE.CatmullRomCurve3(points.map((point) => new THREE.Vector3(...point)))
  const segments = 48
  const sides = 16
  const frames = curve.computeFrenetFrames(segments, false)
  const vertices = []
  const indices = []

  for (let segment = 0; segment <= segments; segment += 1) {
    const t = segment / segments
    const radiusPosition = t * (radii.length - 1)
    const radiusIndex = Math.floor(radiusPosition)
    const radiusMix = radiusPosition - radiusIndex
    const radius = THREE.MathUtils.lerp(
      radii[radiusIndex],
      radii[Math.min(radiusIndex + 1, radii.length - 1)],
      radiusMix,
    )
    const center = curve.getPointAt(t)

    for (let side = 0; side <= sides; side += 1) {
      const angle = (side / sides) * Math.PI * 2
      const normal = frames.normals[segment].clone().multiplyScalar(Math.cos(angle))
      const binormal = frames.binormals[segment].clone().multiplyScalar(Math.sin(angle))
      const vertex = center.clone().addScaledVector(normal, radius).addScaledVector(binormal, radius)
      vertices.push(vertex.x, vertex.y, vertex.z)
    }
  }

  for (let segment = 0; segment < segments; segment += 1) {
    for (let side = 0; side < sides; side += 1) {
      const a = segment * (sides + 1) + side
      const b = a + sides + 1
      indices.push(a, b, a + 1, b, b + 1, a + 1)
    }
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
  geometry.setIndex(indices)
  geometry.computeVertexNormals()
  return geometry
}

function createFallbackParts() {
  return [
    {
      name: 'torso contour',
      geometry: new THREE.LatheGeometry(
        [
          [0, -0.75],
          [0.18, -0.72],
          [0.3, -0.62],
          [0.34, -0.4],
          [0.31, -0.12],
          [0.36, 0.14],
          [0.46, 0.48],
          [0.44, 0.7],
          [0.33, 0.9],
          [0.17, 0.98],
          [0, 0.99],
        ].map(([radius, height]) => new THREE.Vector2(radius, height)),
        48,
      ),
      position: [0, 0.03, 0],
    },
    {
      name: 'neck contour',
      geometry: new THREE.LatheGeometry(
        [
          [0.1, 0.86],
          [0.105, 0.95],
          [0.09, 1.14],
          [0.13, 1.19],
          [0, 1.2],
        ].map(([radius, height]) => new THREE.Vector2(radius, height)),
        32,
      ),
    },
    {
      name: 'head contour',
      region: 'head',
      geometry: new THREE.SphereGeometry(1, 40, 32),
      position: [0, 1.39, 0],
      scale: [0.22, 0.31, 0.2],
    },
    {
      name: 'left arm contour',
      geometry: createTaperedTube(
        [[-0.37, 0.81, 0], [-0.57, 0.64, 0.01], [-0.67, 0.2, 0.04], [-0.79, -0.31, 0.08], [-0.77, -0.64, 0.1]],
        [0.15, 0.13, 0.105, 0.075, 0.045],
      ),
    },
    {
      name: 'right arm contour',
      geometry: createTaperedTube(
        [[0.37, 0.81, 0], [0.57, 0.64, 0.01], [0.67, 0.2, 0.04], [0.79, -0.31, 0.08], [0.77, -0.64, 0.1]],
        [0.15, 0.13, 0.105, 0.075, 0.045],
      ),
    },
    {
      name: 'left leg contour',
      geometry: createTaperedTube(
        [[-0.2, -0.56, 0], [-0.23, -0.78, 0], [-0.28, -1.18, 0.02], [-0.31, -1.59, 0.03], [-0.32, -1.77, 0.05]],
        [0.19, 0.18, 0.135, 0.09, 0.075],
      ),
    },
    {
      name: 'right leg contour',
      geometry: createTaperedTube(
        [[0.2, -0.56, 0], [0.23, -0.78, 0], [0.28, -1.18, 0.02], [0.31, -1.59, 0.03], [0.32, -1.77, 0.05]],
        [0.19, 0.18, 0.135, 0.09, 0.075],
      ),
    },
  ]
}

function FallbackSilhouette({ mode, onSelect }) {
  const parts = useMemo(() => createFallbackParts(), [])
  const wireframe = mode === 'wireframe' || mode === 'anatomy'

  return (
    <group>
      {parts.map(({ name, geometry, position = [0, 0, 0], scale = [1, 1, 1], region }) => (
        <group
          key={name}
          position={position}
          scale={scale}
          onClick={region ? (event) => {
            event.stopPropagation()
            onSelect(region)
          } : undefined}
        >
          <mesh geometry={geometry} scale={1.035} renderOrder={1}>
            <meshBasicMaterial
              color="#5cdcf4"
              side={THREE.BackSide}
              transparent
              opacity={0.045}
              depthWrite={false}
              blending={THREE.AdditiveBlending}
            />
          </mesh>
          <mesh geometry={geometry} renderOrder={2}>
            <meshPhysicalMaterial
              color="#45b9d5"
              emissive="#126277"
              emissiveIntensity={0.9}
              roughness={0.25}
              metalness={0.1}
              transparent
              opacity={mode === 'anatomy' ? 0.11 : 0.2}
              side={THREE.DoubleSide}
              depthWrite={false}
            />
          </mesh>
          <mesh geometry={geometry} scale={1.008} renderOrder={3}>
            <meshBasicMaterial
              color="#76eaff"
              transparent
              opacity={mode === 'wireframe' ? 0.48 : wireframe ? 0.22 : 0.065}
              wireframe
              depthWrite={false}
              blending={THREE.AdditiveBlending}
            />
          </mesh>
        </group>
      ))}
    </group>
  )
}

function AssetModel({ scene, selected, mode, onSelect }) {
  const model = useMemo(() => {
    const clone = scene.clone(true)
    const bounds = new THREE.Box3().setFromObject(clone)
    const size = bounds.getSize(new THREE.Vector3())
    const center = bounds.getCenter(new THREE.Vector3())
    const scale = 3.7 / Math.max(size.y, 0.001)

    clone.position.set(-center.x, -center.y, -center.z)
    clone.scale.setScalar(1)
    clone.traverse((object) => {
      if (!object.isMesh) return
      object.material = Array.isArray(object.material)
        ? object.material.map((material) => material.clone())
        : object.material.clone()
      object.castShadow = true
      object.receiveShadow = true
      const region = getRegion(object)
      if (region) object.userData.region = region
    })

    return { scene: clone, scale }
  }, [scene])

  useEffect(() => {
    setModelMaterials(model.scene, mode, selected)
  }, [mode, model, selected])

  return (
    <group scale={model.scale}>
      <primitive
        object={model.scene}
        onClick={(event) => {
          const region = getRegion(event.object)
          if (region) {
            event.stopPropagation()
            onSelect(region)
          }
        }}
      />
    </group>
  )
}

function RegionHotspot({ region, selected, labels, onSelect }) {
  const active = selected === region
  const ring = useRef()

  useFrame(({ clock }) => {
    if (ring.current) ring.current.rotation.z = clock.elapsedTime * (active ? 0.55 : 0.2)
  })

  return (
    <group position={HOTSPOTS[region]}>
      <mesh
        onClick={(event) => {
          event.stopPropagation()
          onSelect(region)
        }}
      >
        <sphereGeometry args={[0.15, 20, 20]} />
        <meshBasicMaterial
          color={active ? '#ffffff' : '#83efff'}
          transparent
          opacity={active ? 0.2 : 0.055}
          depthWrite={false}
        />
      </mesh>
      <group ref={ring}>
        <mesh
          onClick={(event) => {
            event.stopPropagation()
            onSelect(region)
          }}
        >
          <ringGeometry args={[active ? 0.105 : 0.07, active ? 0.12 : 0.08, 40]} />
          <meshBasicMaterial
            color={active ? '#ffffff' : '#71e7ff'}
            transparent
            opacity={active ? 0.98 : 0.75}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
      <Html
        position={[0.13, 0.12, 0.16]}
        center={false}
        distanceFactor={6}
        style={{
          pointerEvents: labels ? 'auto' : 'none',
          visibility: labels ? 'visible' : 'hidden',
        }}
      >
        <button
          type="button"
          className={`anatomy-label ${active ? 'is-selected' : ''}`}
          aria-label={`Select ${region} region`}
          onClick={(event) => {
            event.stopPropagation()
            onSelect(region)
          }}
        >
          <span>{REGION_LABELS[region]}</span>
          <i />
        </button>
      </Html>
    </group>
  )
}

export default function AnatomyModel({ mode, selected, labels, onSelect, onStatusChange }) {
  const [asset, setAsset] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    const loader = new GLTFLoader()

    fetch(MODEL_PATH, { method: 'HEAD', signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          const error = new Error(`Model request returned ${response.status}`)
          error.status = response.status
          throw error
        }
        if (response.headers.get('content-type')?.includes('text/html')) {
          const error = new Error('Model path returned the application shell instead of a GLB file')
          error.status = 404
          throw error
        }

        loader.load(
          MODEL_PATH,
          (gltf) => {
            if (!active) return
            setAsset(gltf.scene)
            setStatus('ready')
          },
          undefined,
          (error) => {
            if (!active) return
            console.error('Unable to load the astronaut anatomy model.', error)
            setStatus('error')
          },
        )
      })
      .catch((error) => {
        if (!active || error.name === 'AbortError') return
        setStatus(error.status === 404 ? 'missing' : 'error')
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [])

  useEffect(() => {
    onStatusChange(status)
  }, [onStatusChange, status])

  return (
    <group>
      {asset ? (
        <AssetModel scene={asset} selected={selected} mode={mode} onSelect={onSelect} />
      ) : (
        <FallbackSilhouette mode={mode} onSelect={onSelect} />
      )}
      {REGION_ORDER.map((region) => (
        <RegionHotspot
          key={region}
          region={region}
          selected={selected}
          labels={labels}
          onSelect={onSelect}
        />
      ))}
    </group>
  )
}
