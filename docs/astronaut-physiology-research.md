# Astronaut physiology research

**Research owner:** Member 6 - Digital Twin & Research  
**Status:** Initial evidence review complete; clinical review and project-specific protocol remain outstanding  
**Last reviewed:** 2026-11-14

> **Scope and safety:** This document summarizes published research for an educational
> prototype. It is not clinical guidance, a flight rule, a validated risk model,
> or a source of astronaut-specific measurements. The AEGIS project must not
> present synthetic readings as NASA data or use this summary to diagnose,
> triage, or make operational decisions.

## Purpose

This review describes cardiovascular adaptations relevant to a human-spaceflight
digital twin: headward fluid redistribution, circulating-volume changes,
orthostatic intolerance, cardiovascular deconditioning, and the context needed
to interpret heart rate and blood pressure. It identifies design implications
for AEGIS without defining clinical thresholds or prescribing countermeasures.

## Evidence summary

### Headward fluid shift

On Earth, gravity creates a head-to-foot hydrostatic pressure gradient. In
microgravity, that gradient is greatly reduced, and body fluids redistribute
toward the head and torso. Acute weightlessness is associated with central
volume expansion; the direction of fluid movement is not the same as creating
additional body fluid. NASA's review also describes fluid shifts and later
cardiovascular changes during sustained exposure.

**Interpretation for AEGIS:** A visual explanation may describe redistribution
as a response to altered gravity. Do not infer the size of an individual's
fluid shift from a single heart-rate, blood-pressure, or oxygen reading.

### Blood and plasma volume

NASA's review describes sustained microgravity exposure and fluid
redistribution as associated with reductions in total blood volume and notes
reduced plasma volume as one proposed explanation for some historical
postflight exercise-response changes. These are related but distinct
measurements: plasma volume is not interchangeable with total blood volume.
The sources reviewed here do not establish one universal amount or time course
that can be applied to every astronaut.

**Interpretation for AEGIS:** Do not calculate or display a personalized blood
or plasma volume from the dashboard's vital signs. Keep such a value absent
unless a validated measurement and its collection context are supplied.

### Cardiovascular adaptation and deconditioning

The cardiovascular system is adapted to Earth's upright posture. NASA reports
that changes associated with altered gravity can begin early and that
measurable physiological decrements have been observed within days. The degree
of deconditioning varies with factors including mission duration, age, sex,
fitness, and gravity environment. Exercise is an established spaceflight
countermeasure, but this research summary does not prescribe an individual
exercise plan.

In an in-flight study of eight male ISS astronauts measured between 85 and 192
days in space, Norsk and colleagues reported lower 24-hour ambulatory blood
pressure and higher stroke volume and cardiac output than preflight, while
heart rate was unchanged. These results illustrate that an in-flight
cardiovascular response should not be reduced to the assumption that heart
rate always rises or blood pressure always falls.

### Orthostatic intolerance after return to gravity

When a crew member returns to an upright gravitational environment, blood
redistributes toward the lower body. Reduced circulating volume, changes in
stroke volume and vascular responses, and altered cardiovascular regulation
may contribute to difficulty maintaining blood pressure while standing.
Orthostatic intolerance (OI) is not uniform across crew members, and the
measured response depends on flight duration, time since landing, posture,
activity, and test protocol.

Mastrandrea and colleagues studied seven astronauts (one woman) before and
after long-duration missions averaging 146 days (standard deviation 43 days).
Testing took place within hours of landing, with participants largely kept
supine before measurement. The study reported lower postflight resting stroke volume and
higher total peripheral resistance, without a significant resting heart-rate
change. Its lower-body-negative-pressure testing did not show a significant
change in the measured arterial or cardiopulmonary baroreflex responses. This
small, early-postflight study is evidence of specific responses in that cohort,
not a universal pattern or diagnostic rule for all astronauts.

### Heart rate and blood pressure are context-dependent

The reviewed evidence differs across in-flight and postflight measurements.
For example, the Norsk study measured eight male astronauts during long-duration
flight, whereas the Mastrandrea study measured seven astronauts shortly after
landing. The populations, posture, mission phase, and protocols differ.
Therefore:

- Do not assume one fixed direction of change for heart rate or blood pressure.
- Do not label a reading abnormal based on this research summary.
- Preserve the measurement's units, timestamp, posture/activity context, and
  mission phase when those data are available.
- Interpret trends against an approved, individual-specific clinical protocol;
  none is defined by this document.

## AEGIS design implications

These are research-informed product recommendations, not validated clinical
requirements:

1. **Keep provenance visible.** Mark demonstration values as synthetic. Do not
   imply they are live telemetry, NASA data, a crew member's record, or
   clinically validated.
2. **Retain context with readings.** Where the future data contract allows,
   record units, timestamp/time zone, mission phase, posture, activity, and
   source. Missing context should remain missing rather than be silently
   invented.
3. **Prefer trends and explanatory context over diagnosis.** A single vital
   sign does not establish fluid shift, deconditioning, OI, or another
   condition.
4. **Do not invent thresholds.** No universal AEGIS alert limits, diagnostic
   categories, or exercise prescriptions are established by this research
   summary. These require the appropriate clinical and mission authorities.
5. **Keep synthetic data separate.** Synthetic scenarios may demonstrate the
   interface, but their values and labels must not be presented as observations
   from NASA missions or as evidence that the UI can detect a medical risk.

## Evidence limitations and open questions

- Spaceflight cohorts are small and often have limited representation across
  sex, age, mission type, and health background.
- In-flight and postflight studies use different postures, instruments,
  protocols, and time points; their results should not be treated as directly
  interchangeable.
- The 2024 postflight study included seven participants, with only five
  available for some signal analyses. It assessed a specific early-return
  window and a lower-body-negative-pressure protocol.
- The 2015 in-flight study included eight male astronauts. Its results cannot
  establish the same response for all crew members.
- A NASA technical review synthesizes previous research; individual historical
  findings may have their own population and protocol limitations.
- This review does not establish current NASA clinical thresholds, individual
  baselines, countermeasure eligibility, or a validated predictive model.
- Before AEGIS uses real astronaut data or communicates risk, the team needs a
  defined data source and license, collection protocol, clinical review, and
  approved interpretation and escalation rules.

## Sources

1. Taoufik, S. D., Coffey, K. M., & Francisco, D. R. (2025). *Astronaut
   Physiological Deconditioning and Exercise Prescription Countermeasures in
   Spaceflight*. NASA/SP-20250000273. NASA Office of the Chief Health and
   Medical Officer.
   [NASA Technical Reports Server record](https://ntrs.nasa.gov/citations/20250000273);
   [NASA-hosted text](https://ntrs.nasa.gov/api/citations/20250000273/downloads/SP%2020250000273%20SUBMISSION.docx.txt).
   Supports the overview of altered-gravity deconditioning, fluid
   redistribution, individual variability, and exercise as a countermeasure.
2. Norsk, P., Asmar, A., Damgaard, M., & Christensen, N. J. (2015). Fluid
   shifts, vasodilatation and ambulatory blood pressure reduction during long
   duration spaceflight. *The Journal of Physiology, 593*(3), 573-584.
   [https://doi.org/10.1113/jphysiol.2014.284869](https://doi.org/10.1113/jphysiol.2014.284869)
   [PubMed record](https://pubmed.ncbi.nlm.nih.gov/25774397/);
   [Open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4324706/).
   Supports the in-flight fluid-shift, blood-pressure, stroke-volume, cardiac
   output, and heart-rate example; the study cohort was eight male astronauts.
3. Mastrandrea, C. J., Greaves, D. K., Shoemaker, J. K., Blaber, A. P.,
   Arbeille, P., & Hughson, R. L. (2024). Lower body negative pressure
   identifies altered central vein characteristics without accompanying
   changes to baroreflexes in astronauts within hours of landing. *Scientific
   Reports, 14*, 1215.
   [https://doi.org/10.1038/s41598-024-51643-1](https://doi.org/10.1038/s41598-024-51643-1)
   [Open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10786840/).
   Supports the early-postflight cohort and study-specific cardiovascular
   findings and limitations.
4. NASA Human Research Program. *Human Research Roadmap* and current
   *Integrated Research Plan*.
   [Roadmap](https://humanresearchroadmap.nasa.gov/);
   [Integrated Research Plan](https://humanresearchroadmap.nasa.gov/Documents/IRP_Rev-Current.pdf).
   Establishes NASA's program context for investigating and mitigating
   astronaut health and performance risks; it is not a source of AEGIS
   thresholds or personal medical advice.

## Phase 1: Brain and Nervous System

**Status:** Initial evidence review complete; clinical and operational review
remain outstanding  
**Last reviewed:** 2026-11-14

### Spaceflight-Associated Neuro-ocular Syndrome (SANS)

NASA describes SANS as a set of new ocular findings observed in some astronauts
after long-duration spaceflight. Findings used in the NASA clinical update
include optic disc edema, chorioretinal folds, posterior globe flattening, and
a hyperopic (far-sighted) refractive shift. NASA's 2022 NTRS clinical-update
abstract explicitly describes SANS pathogenesis as unclear and notes that the
severity or duration that makes a finding pathological was not established.
These are clinical eye findings, not a generic diagnosis of brain disease.

A prospective study of 11 astronauts during approximately six-month ISS
missions measured changes in the optic nerve head rim and peripapillary
choroid, as well as a postflight reduction in axial length that remained
measurable at one year. This supports the occurrence of measurable ocular
structural changes in that cohort; it does not mean every astronaut develops
the same findings or a clinically meaningful loss of vision.

### Headward fluid shift: proposed mechanism, not a complete explanation

Loss of the normal head-to-foot hydrostatic gradient redistributes fluids
toward the head and torso. Headward fluid shift is one proposed contributor to
SANS: altered vascular and cerebrospinal-fluid dynamics could affect the
mechanical environment around the optic nerve and posterior eye. This is a
mechanistic hypothesis, not proof that a single pressure change causes SANS.

The uncertainty is important. A longitudinal MRI study of 10 astronauts found
no significant average postflight changes in its measured optic-nerve and
optic-nerve-sheath metrics, although one participant with optic disc edema had
an increased sheath area. A separate 10-astronaut study measured posterior
globe displacement over a year and reported incomplete average recovery of
that structural measure at the final time point. These results concern
different structures and methods; they cannot establish one universal
intracranial-pressure mechanism or clinical course.

The NASA clinical update also cautions that observed brain-anatomy changes
were being monitored and had not been linked to SANS or functional decrements
in that report. Later research has reported associations between selected
preflight cortical-thickness measures and postflight motor/balance outcomes.
Such associations are not proof that a brain structural change causes a
specific symptom, nor do they provide an individual clinical prediction.

### Vestibular and sensorimotor adaptation

The vestibular system helps the brain estimate movement and orientation.
Microgravity changes the relationship between vestibular, visual, and
proprioceptive cues, so the nervous system must adapt to a new sensory
environment. NASA's Human Research Roadmap identifies possible manifestations
of altered sensorimotor/vestibular function, including motion sickness,
spatial disorientation, changes in postural control and locomotion, and
manual or fine-motor performance decrements. NASA notes potential relevance
to tasks such as vehicle control, EVA, and emergency egress during and
following transitions.

After return to Earth's gravity, the in-flight adaptation is no longer fully
appropriate. A 2024 peer-reviewed study developed a ground-based disorientation
analog and compared it with the immediate postflight experience of five
previously flown astronauts. It supports the relevance of interacting
vestibular and proprioceptive cues to postflight performance, but the small
sample and analog design do not establish clinical prevalence, recovery time,
or an individual's risk.

### Cognitive performance, sleep, and fatigue

Sleep and fatigue can affect alertness and neurobehavioral performance, but
they are not measured by the AEGIS vital signs listed below. A NASA-supported
study analyzed repeated three-minute Psychomotor Vigilance Test (PVT)
measurements and self-reported, cognitive, and environmental data from 24
astronauts on six-month ISS missions. In its model, prior PVT performance,
reported fatigue and stress, temperature, and radiation exposure were among
the important predictors of alertness. These are associations in a specific
dataset, not a diagnostic test or proof that any one factor caused a
performance change.

This section records the overlap with sleep and fatigue because they can
affect cognition. A fuller review of sleep, stress, and circadian rhythm is a
separate later research task; this section does not claim to complete it.

### Visual and sensorimotor adaptation after landing

Postflight adaptation is system- and person-specific. In the 11-astronaut
ocular study, some measured structural changes remained at follow-up through
one year. In a separate study of 10 astronauts, MRI-derived posterior globe
displacement was still present on average at the final one-year measurement,
although it had partially changed across earlier follow-ups. A study of
postflight motor and balance performance found that selected whole-brain
cortical-thickness measures were associated with recovery-from-fall and
balance outcomes in its cohort. None of these findings defines a universal
recovery duration or should be used to predict an individual crew member's
function.

### Educational content for the AEGIS Brain / Head region

Suggested explanatory copy for future product documentation or a clinician-
reviewed interface:

> **Brain and head in spaceflight:** Altered gravity changes vestibular and
> visual orientation cues, and body fluids redistribute toward the head and
> torso. Some long-duration astronauts show ocular structural findings grouped
> under Spaceflight-Associated Neuro-ocular Syndrome (SANS). Headward fluid
> shift is one proposed contributor, but SANS mechanisms and individual
> outcomes remain under study. Postflight balance and sensorimotor adaptation
> vary. The AEGIS demonstration readings do not assess vision, brain function,
> balance, or SANS.

This copy is educational context only, not medical advice, screening, diagnosis,
or a claim that the digital twin can measure these changes. Any eventual
visual-region mapping or product wording requires review by Member 5 for UI
integration and by appropriate clinical/scientific reviewers for accuracy.

### What the current synthetic dashboard can and cannot indicate

The current dashboard displays four synthetic demonstration metrics: heart
rate, oxygen saturation (SpO2), body temperature, and respiratory rate. They
are generated for interface demonstration, not supplied by a live sensor
feed, NASA telemetry, or measurements from a real individual. The current
dashboard does not display blood pressure.

Blood pressure is also absent from the shared synthetic sample, generated
CSV/latest JSON, grouped backend reading schema, and backend's accepted sensor
measurement types. A local or older mock UI may show a value such as 118/76
mmHg, but that is a presentation-only fixture, not a backend measurement or
part of the shared data contract. Do not interpret it as an astronaut's
reading.

The current frontend describes the head view as educational and states that
it does not provide a neurological assessment. Any older/local mock UI wording
such as "Neurological status: Normal" is unsupported by these synthetic
inputs and must not be treated as a measured result.

These dashboard inputs **cannot** establish or rule out SANS, optic-disc
edema, refractive change, intracranial pressure, a vestibular disorder,
spatial disorientation, balance impairment, fatigue, sleep loss, cognitive
impairment, or a neurological disease. The dashboard does not collect visual
acuity, refraction, ocular imaging (such as OCT or MRI), vestibular function,
postural control, sleep duration, or a PVT/cognitive task. A heart-rate value
is nonspecific and cannot substitute for those assessments. No local mock
blood-pressure value can substitute for these assessments either. The
existing values must not be relabeled as neurological status or used to make
health or mission decisions.

### Evidence limits and open questions

- SANS remains an active research area. The underlying mechanisms and the
  clinical meaning of the range and duration of findings are not settled.
- The NASA NTRS SANS prevalence figures are explicitly preliminary values in
  a 2022 conference abstract. The abstract does not establish a universal,
  current prevalence estimate; do not use those percentages as an AEGIS risk
  probability.
- Prospective astronaut cohorts are small and have limited representation.
  Findings from 10 or 11 participants cannot establish universal outcomes.
- Imaging measures, mission duration, time since landing, instruments, and
  study protocols differ. Structural imaging changes are not interchangeable
  with visual symptoms or functional impairment.
- Vestibular analog studies and correlations between brain imaging and
  performance do not establish a clinical screening or predictive tool.
- The cognitive-performance study is observational/modeling research using
  repeated PVT data; its predictors are not clinical biomarkers or diagnoses.
- No AEGIS neurological/visual thresholds, alerts, clinical pathways, or
  validated models are defined by this review.

### Brain and nervous system sources

1. NASA Human Research Program. (2025). *Risk of Altered
   Sensorimotor/Vestibular Function Impacting Critical Mission Tasks, Human
   Health, and Long-Term Health*. Human Research Roadmap, risk last published
   May 13, 2025; the page reports Human System Risk Board approval in November
   2024. [Risk statement](https://humanresearchroadmap.nasa.gov/Risks/risk.aspx?i=88).
   Supports NASA's identified sensorimotor manifestations and mission-task
   relevance; risk characterization is not an individual diagnosis.
2. Brunstetter, T. J., et al. (2022). *Spaceflight Associated Neuro-ocular
   Syndrome (SANS): 2022 Clinical Update*. NASA Technical Reports Server,
   20220000516. [NTRS record](https://ntrs.nasa.gov/citations/20220000516).
   NASA NTRS classifies the record as a presentation from the 2022 Human
   Research Program Investigators Workshop. It supports the clinical signs
   and states that pathogenesis and pathological thresholds were unclear in
   that update.
   The reported prevalence values are preliminary and should not be generalized.
3. Macias, B. R., et al. (2020). Association of Long-Duration Spaceflight With
   Anterior and Posterior Ocular Structure Changes in Astronauts and Their
   Recovery. *JAMA Ophthalmology, 138*(5), 553-559.
   [https://doi.org/10.1001/jamaophthalmol.2020.0673](https://doi.org/10.1001/jamaophthalmol.2020.0673)
   · [PubMed](https://pubmed.ncbi.nlm.nih.gov/32239198/).
   Prospective longitudinal study of 11 astronauts; supports measured ocular
   structural changes and follow-up through one year.
4. Sater, S. H., et al. (2021). Automated MRI-based quantification of
   posterior ocular globe flattening and recovery after long-duration
   spaceflight. *Eye, 35*, 1869-1878.
   [https://doi.org/10.1038/s41433-021-01408-1](https://doi.org/10.1038/s41433-021-01408-1)
   · [PubMed](https://pubmed.ncbi.nlm.nih.gov/33514895/).
   Longitudinal MRI study of 10 astronauts; supports a measured structural
   change and incomplete average resolution at one year, not a universal
   clinical course.
5. Rohr, J. J., et al. (2020). Quantitative magnetic resonance image assessment
   of the optic nerve and surrounding sheath after spaceflight. *npj
   Microgravity, 6*, 30.
   [https://doi.org/10.1038/s41526-020-00119-3](https://doi.org/10.1038/s41526-020-00119-3)
   · [PubMed](https://pubmed.ncbi.nlm.nih.gov/33083526/).
   Longitudinal study of 10 astronauts; average measured optic-nerve and sheath
   changes were not significant, illustrating uncertainty in a simple
   intracranial-pressure explanation.
6. Moudy, S. C., et al. (2024). Development of a ground-based sensorimotor
   disorientation analog to replicate astronaut postflight experience.
   *Frontiers in Physiology, 15*, 1369788.
   [https://doi.org/10.3389/fphys.2024.1369788](https://doi.org/10.3389/fphys.2024.1369788)
   · [PubMed](https://pubmed.ncbi.nlm.nih.gov/38699143/).
   Analog study comparing a test battery with five previously flown astronauts;
   informs postflight sensorimotor research but is not a population or clinical
   validation study.
7. Koppelmans, V., et al. (2022). Cortical thickness of primary motor and
   vestibular brain regions predicts recovery from fall and balance directly
   after spaceflight. *Brain Structure and Function, 227*(6), 2073-2086.
   [https://doi.org/10.1007/s00429-022-02492-z](https://doi.org/10.1007/s00429-022-02492-z)
   · [PubMed](https://pubmed.ncbi.nlm.nih.gov/35469104/).
   Study of 14 astronauts; selected whole-brain cortical-thickness measures
   were associated with postflight motor/balance outcomes. Association does
   not establish causality or individual prediction.
8. Tu, D., et al. (2022). Dynamic ensemble prediction of cognitive performance
   in spaceflight. *Scientific Reports, 12*, 11032.
   [https://doi.org/10.1038/s41598-022-14456-8](https://doi.org/10.1038/s41598-022-14456-8)
   · [PubMed](https://pubmed.ncbi.nlm.nih.gov/35773291/).
   Observational modeling study using repeated PVT data from 24 astronauts on
   six-month ISS missions; predictors are associations, not clinical
   indicators.
9. Clark, T. K., et al. (2016). *Relationships Between Vestibular Measures as
   Potential Predictors for Spaceflight Sensorimotor Adaptation*. NASA
   Technical Reports Server, 20150023270.
   [NTRS record](https://ntrs.nasa.gov/citations/20150023270).
   Conference abstract reporting ground-based measures in 15 control subjects;
   it describes research aims and individual variability, not a validated
   astronaut predictor.

## Phase 2: Remaining astronaut physiology systems

The following chapters are initial evidence reviews for educational and
prototype-design use. They do not define clinical thresholds, establish a
specific crew member's health state, or constitute clinical review.

### Respiratory system

Gravity affects the distribution of ventilation and blood flow within the
lungs. Removing the usual vertical hydrostatic gradients in microgravity
changes pulmonary perfusion and related measurements; the direction and size
of a measured response depend on the measure, mission phase, and study
protocol. In a short-duration flight study of four participants, pulmonary
tissue volume and diffusing-capacity measurements changed over the course of
flight, but the authors did not find evidence of interstitial pulmonary edema.
That small study is not evidence that every respiratory variable changes in
the same way or that a single pattern applies to long-duration missions.

**Established observation:** Pulmonary physiology is gravity-sensitive, and
spaceflight studies have measured changes in pulmonary tissue and gas-transfer
variables.

**Interpretation and uncertainty:** A change in SpO2 or respiratory rate alone
cannot identify a pulmonary mechanism, fluid shift, or disease. The studies
reviewed here do not establish AEGIS respiratory thresholds or a clinically
meaningful individual risk estimate.

**AEGIS implication:** The current demo contains one synthetic SpO2 value and
one synthetic respiration-rate value. It has no flow or volume waveform,
spirometry, gas-exchange protocol, activity/posture context, or validated
mission data. Present those fields only as fabricated demonstrations, not
respiratory-system assessment.

### Musculoskeletal system

Reduced gravitational loading changes the mechanical stimulus to the skeleton
and skeletal muscle. Long-duration spaceflight research has documented bone
and muscle changes, including changes in bone mineral measures, muscle size,
strength, and aerobic capacity. These measures differ by body site, person,
countermeasure, and timing. A NASA-associated study of 13 ISS crewmembers
reported that ARED exercise together with adequate energy intake and vitamin
D status was associated with maintenance of bone mineral density at most
measured regions in that cohort; it does not establish a universal
prescription or guarantee protection for an individual.

**Established observation:** Unloading is associated with musculoskeletal
deconditioning, and exercise and nutrition are studied countermeasures.
Countermeasures do not make all outcomes identical or prove a person's bone
or muscle status from vital signs.

**Interpretation and uncertainty:** Bone mineral density, bone turnover,
muscle strength, muscle size, injury risk, and physical performance are
distinct outcomes. A posture or limb-region selection is not a measurement of
any of them. The reviewed sources do not support personalized fracture,
osteoporosis, strength, or exercise advice in AEGIS.

**AEGIS implication:** Do not map HR, SpO2, temperature, BP, or respiration
values to muscle or bone health. If future data are added, preserve the
specific measurement, method, site, timestamp, mission phase, and source.

### Abdominal and metabolic systems

The abdomen is a body region, not one physiological system: it contains
multiple organs and tissues. The reviewed spaceflight sources support
discussion of headward fluid redistribution, nutrition, energy intake, and
body-composition measurements, but they do not justify presenting a single
"abdominal health" score. In a small ISS cohort study, researchers measured
body mass, body composition, dietary intake, bone density, and biochemical
markers together; this illustrates why body mass alone cannot substitute for
body composition, nutritional status, or organ-specific assessment.

**Established observation:** Spaceflight studies examine nutrition and body
composition alongside other physiological outcomes, and gravity-related
fluid redistribution affects where fluid is distributed. These facts do not
demonstrate a specific abdominal-organ disease or a universal metabolic
change.

**Interpretation and uncertainty:** A synthetic temperature or systemic vital
sign cannot measure liver, pancreas, kidney, gastrointestinal, endocrine, or
metabolic function. The present project has no validated abdominal or
metabolic data source, sampling protocol, reference population, or clinical
interpretation.

**AEGIS implication:** Treat "abdomen" as an educational anatomical selection
only. Do not assign temperature or other systemic values as abdominal-organ
readings or create a synthetic metabolic score.

### Radiation and immune health

Space radiation is a distinct exposure from ordinary clinical vital signs.
NASA's 2026 evidence report identifies ionizing-radiation health concerns
including carcinogenesis, acute radiation effects, and possible central
nervous-system and cardiovascular outcomes; risk assessment depends on
exposure and mission context and is not inferred from HR, SpO2, or a body
region. A radiation-dose estimate is not a direct observation of disease.

Spaceflight immune research reports changes in some immune measures and
reactivation of latent herpesviruses during long-duration missions. Immune
responses are complex and may differ between innate and adaptive components.
NASA's NTRS record on neutrophil-to-lymphocyte ratio explicitly notes that
this ratio had not been established as a predictor of astronaut health in
spaceflight; it must not be presented as a validated AEGIS biomarker.
Radiation, altered gravity, sleep, stress, nutrition, and other exposures
may co-occur, so an observed association does not isolate a single cause.

**Established observation:** NASA and peer-reviewed research identify
radiation and immune response as active human-spaceflight research areas.
Selected immune changes have been observed in cohorts, but those findings do
not provide an individual diagnosis or a simple "immune status" measure.

**Interpretation and uncertainty:** Radiation dose models, immune assays,
clinical outcomes, and mission exposure histories are different kinds of
evidence. The project has no personal dose record, radiation transport model,
immune laboratory results, or approved clinical rule.

**AEGIS implication:** Do not turn synthetic vital signs into radiation dose,
cancer probability, infection status, immune score, or radiation warning.
Use radiation and immune copy as general educational context only and keep
uncertainty visible.

### Sleep, stress, and circadian rhythms

NASA's sleep-risk evidence review reports that astronauts average less sleep
during spaceflight than on the ground, while noting that causes and
individual vulnerability are not fully resolved. Irregular schedules,
circadian misalignment, environmental conditions, work demands, and
individual differences are relevant research factors. NASA notes that
circadian phase biomarkers are not readily available for routine in-flight
measurement. Sleep loss and circadian misalignment may affect alertness and
performance, but this does not make a short performance measure or a vital
sign a sleep diagnosis.

**Established observation:** Sleep duration, schedules, fatigue, and
circadian-related conditions are studied in astronaut health and performance.
An observational study of 64 astronauts documented sleep deficiency and
hypnotic use before, during, and after spaceflight; its design does not
establish that a single environmental factor caused a given outcome.

**Interpretation and uncertainty:** Sleep duration, sleep quality, circadian
phase, fatigue, stress, and cognitive performance are related but non-
interchangeable. The current demo does not collect actigraphy, sleep logs,
light exposure, schedule history, fatigue reports, or validated performance
tests.

**AEGIS implication:** Do not infer restedness, circadian phase, stress, or
fitness for duty from the five synthetic vital fields. Any future sleep or
fatigue display must identify its actual measurement and remain separate from
diagnostic or mission-readiness claims.
