import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js'
import { applyAnatomyStyle, prepareAnatomyModel } from './anatomyScene.js'

const MODEL_PATH = '/models/adora-anatomy.glb'

async function loadModel(signal) {
  const response = await fetch(MODEL_PATH, { signal })
  if (!response.ok) {
    const error = new Error(`Model request returned ${response.status}`)
    error.status = response.status
    throw error
  }

  if (response.headers.get('content-type')?.includes('text/html')) {
    const error = new Error('Model path returned HTML instead of a GLB file')
    error.status = 404
    throw error
  }

  const loader = new GLTFLoader()
  loader.setMeshoptDecoder(MeshoptDecoder)

  const arrayBuffer = await response.arrayBuffer()
  return new Promise((resolve, reject) => {
    loader.parse(
      arrayBuffer,
      `${window.location.origin}/`,
      resolve,
      reject,
    )
  })
}

function FallbackSilhouette() {
  return (
    <group>
      <mesh position={[0, 0.1, 0]}>
        <capsuleGeometry args={[0.42, 1.6, 8, 24]} />
        <meshBasicMaterial
          color="#58cfe9"
          transparent
          opacity={0.12}
          wireframe
          depthWrite={false}
        />
      </mesh>
      <mesh position={[0, 1.15, 0]}>
        <sphereGeometry args={[0.25, 24, 16]} />
        <meshBasicMaterial
          color="#58cfe9"
          transparent
          opacity={0.16}
          wireframe
          depthWrite={false}
        />
      </mesh>
    </group>
  )
}

function LoadedModel({ scene, mode, layer, selected, regionStatuses, onSelect, onModelInfo, reducedMotion, isDemo }) {
  const model = useMemo(() => prepareAnatomyModel(scene), [scene])
  const criticalMaterials = useRef([])
  const invalidate = useThree((state) => state.invalidate)

  useLayoutEffect(() => {
    criticalMaterials.current = applyAnatomyStyle(model, { mode, selected, regionStatuses, layer, isDemo })
    invalidate()
  }, [model, mode, regionStatuses, selected, layer, isDemo, invalidate])

  useFrame(({ clock }) => {
    if (reducedMotion) return
    const pulse = 0.82 + Math.sin(clock.elapsedTime * 5) * 0.18
    criticalMaterials.current.forEach((material) => {
      material.emissiveIntensity = material.userData.aegisAlertIntensity * pulse
    })
  })

  useEffect(() => {
    onModelInfo(model.info)
    return () => {
      model.clonedMaterials.forEach((material) => material.dispose())
    }
  }, [model, onModelInfo])

  return (
    <group scale={model.scale}>
      <primitive
        object={model.scene}
        onClick={(event) => {
          if (event.delta > 5) return
          const selection = event.object.userData.aegisSelection
          if (selection && event.object.userData.aegisPickable) {
            event.stopPropagation()
            onSelect(selection)
          }
        }}
      />
    </group>
  )
}

export default function AnatomyModel({
  mode,
  layer,
  selected,
  regionStatuses,
  onSelect,
  onStatusChange,
  onModelInfo,
  reducedMotion = false,
  isDemo = true,
}) {
  const [asset, setAsset] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    loadModel(controller.signal)
      .then((gltf) => {
        if (!active) return
        setAsset(gltf.scene)
        setStatus('ready')
      })
      .catch((error) => {
        if (!active || error.name === 'AbortError') return
        const missing = error.status === 404
        setStatus(missing ? 'missing' : 'error')
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [])

  useEffect(() => {
    onStatusChange(status)
    if (status !== 'ready') onModelInfo({})
  }, [onModelInfo, onStatusChange, status])

  return (
    <group>
      {asset ? (
        <LoadedModel
          scene={asset}
          mode={mode}
          layer={layer}
          selected={selected}
          regionStatuses={regionStatuses}
          onSelect={onSelect}
          onModelInfo={onModelInfo}
          reducedMotion={reducedMotion}
          isDemo={isDemo}
        />
      ) : (
        <FallbackSilhouette />
      )}
    </group>
  )
}
