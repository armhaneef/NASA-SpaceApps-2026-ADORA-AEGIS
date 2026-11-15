const HEAD_MESHES = new Set([
  'skull',
  'eye_l',
  'eye_r',
  'cranial_nerves',
])

const BRAIN_MESHES = new Set([
  'brain',
  'brainstem',
  'cerebellum',
])

const ABDOMEN_MESHES = new Set([
  'liver',
  'colon',
  'small_intestine',
  'stomach',
  'gallbladder',
  'appendix',
  'spleen',
  'pancreas',
  'kidney_l',
  'kidney_r',
  'bladder',
])

const ARM_PARTS = /arm|shoulder|forearm|hand|deltoid|biceps|triceps|humerus|radius|ulna|wrist|clavicle/i
const LEG_PARTS = /leg|foot|thigh|calf|femur|tibia|fibula|patella|ankle|knee|hip|shin|adductor|hamstring|quadriceps|gluteal|iliopsoas/i

export function getAnatomyRegion(name) {
  if (typeof name !== 'string') return null
  const identifier = name.toLowerCase()

  if (HEAD_MESHES.has(identifier)) return 'head'
  if (BRAIN_MESHES.has(identifier)) return 'brain'
  if (identifier === 'heart' || identifier === 'coronary_arteries') return 'heart'
  if (identifier === 'lung_l') return 'leftLung'
  if (identifier === 'lung_r') return 'rightLung'
  if (ABDOMEN_MESHES.has(identifier)) return 'abdomen'

  const side = identifier.endsWith('_l') ? 'left' : identifier.endsWith('_r') ? 'right' : null
  if (side && ARM_PARTS.test(identifier)) return `${side}Arm`
  if (side && LEG_PARTS.test(identifier)) return `${side}Leg`

  return null
}
