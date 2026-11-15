const HEAD_MESHES = new Set([
  'skull',
  'eye_l',
  'eye_r',
  'cranial_nerves',
  'mandible',
  'teeth',
  'arteries_head',
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
  // These GLB assemblies cross the neck/torso and arm. Coloring the whole
  // assembly would falsely spread a localized arm marker into the torso.
  if (/^shoulder_muscles_[lr]$/.test(identifier)) return null

  if (HEAD_MESHES.has(identifier)) return 'head'
  if (BRAIN_MESHES.has(identifier)) return 'brain'
  if (identifier === 'heart' || identifier === 'coronary_arteries') return 'heart'
  if (identifier === 'lung_l') return 'leftLung'
  if (identifier === 'lung_r') return 'rightLung'
  if (ABDOMEN_MESHES.has(identifier)) return 'abdomen'
  if (identifier === 'abdominal_muscles') return 'abdomen'

  const side = identifier.endsWith('_l') ? 'left' : identifier.endsWith('_r') ? 'right' : null
  if (side && (ARM_PARTS.test(identifier) || /rotator_cuff|scapula/.test(identifier))) return `${side}Arm`
  if (side && LEG_PARTS.test(identifier)) return `${side}Leg`

  return null
}

// Exact mesh names inspected in the existing asset. No geometry is synthesized.
const ORGAN_NAMES = {
  liver: ['liver', 'Liver', 'abdomen'],
  kidney_l: ['leftKidney', 'Left kidney', 'abdomen'],
  kidney_r: ['rightKidney', 'Right kidney', 'abdomen'],
  stomach: ['stomach', 'Stomach', 'abdomen'],
  spleen: ['spleen', 'Spleen', 'abdomen'],
  pancreas: ['pancreas', 'Pancreas', 'abdomen'],
  gallbladder: ['gallbladder', 'Gallbladder', 'abdomen'],
  small_intestine: ['smallIntestine', 'Small intestine', 'abdomen'],
  colon: ['colon', 'Colon', 'abdomen'],
  appendix: ['appendix', 'Appendix', 'abdomen'],
  bladder: ['bladder', 'Bladder', 'abdomen'],
  adrenal_l: ['leftAdrenal', 'Left adrenal gland', 'abdomen'],
  adrenal_r: ['rightAdrenal', 'Right adrenal gland', 'abdomen'],
  ureter_l: ['leftUreter', 'Left ureter', 'abdomen'],
  ureter_r: ['rightUreter', 'Right ureter', 'abdomen'],
  reproductive: ['reproductive', 'Reproductive structures', null],
  prostate: ['prostate', 'Prostate', null],
  eye_l: ['leftEye', 'Left eye', 'head'],
  eye_r: ['rightEye', 'Right eye', 'head'],
  pituitary: ['pituitary', 'Pituitary gland', 'brain'],
  tongue: ['tongue', 'Tongue', 'head'],
  salivary_glands: ['salivaryGlands', 'Salivary glands', 'head'],
  larynx: ['larynx', 'Larynx', null],
  pharynx: ['pharynx', 'Pharynx', null],
  esophagus: ['esophagus', 'Esophagus', null],
  thymus: ['thymus', 'Thymus', null],
  bronchi: ['bronchi', 'Bronchi', null],
  trachea: ['trachea', 'Trachea', null],
}

export const ORGAN_STRUCTURES = Object.fromEntries(Object.entries(ORGAN_NAMES).map(([mesh, [id, name, region]]) => [id, {
  name, shortName: name.toUpperCase(), code: `GLB / ${mesh}`, mesh, region,
  description: `Verified ${mesh} mesh in the supplied educational model.`,
  explanation: `${name} is shown in its original model position. No regional sensor measurement or clinical assessment is available.`,
}]))

export function getAnatomySelection(name) {
  return ORGAN_NAMES[name]?.[0] ?? getAnatomyRegion(name)
}

export function getSelectionRegion(selection) {
  return ORGAN_STRUCTURES[selection]?.region ?? selection
}

export function getSelectionStatus(statuses, selection) {
  const candidates = [statuses[selection], statuses[getSelectionRegion(selection)]]
  return ['critical', 'warning', 'normal', 'no-data'].find((status) => candidates.includes(status)) ?? 'no-data'
}

export function getLocalizedFindings(alerts, selection) {
  if (!selection) return []
  return alerts.filter((alert) => alert.source === 'demo-region-simulation'
    && (alert.region === selection || alert.region === getSelectionRegion(selection)))
}
