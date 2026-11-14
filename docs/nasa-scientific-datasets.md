# NASA Scientific Dataset Research for AEGIS

**Owner:** Member 6 - Digital Twin & Research  
**Reviewed:** 2026-11-14  
**Purpose:** Identify credible NASA space-life-science research sources and
document safe dataset-selection rules. This is a source inventory, not an
authorization to ingest or redistribute human-subject data.

## Summary

The NASA Open Science Data Repository (OSDR) is the best first catalog for
space-life-science research. NASA describes OSDR as containing multi-modal
research data and metadata, including omics, phenotypic, physiological,
behavioral, biomedical, bioimaging, environmental telemetry, hardware, and
tabular, text, code, image, and video data. It includes GeneLab and the Ames
Life Sciences Data Archive (ALSDA), and the portal exposes multiple record
types, including study, experiment, subject, biospecimen, and payload.

OSDR is a research repository, not a feed of live astronaut vital signs. A
catalog entry may concern human samples, animal models, cells, plants,
microbes, a ground analog, a spaceflight mission, or a mixture of study
material. The organism, sample, experiment, conditions, and mission phase must
be checked in the record and publication before interpreting a dataset.

## Source inventory

| Source | What it provides | Relevant data types | Access and use notes |
|---|---|---|---|
| [NASA OSDR search portal](https://osdr.nasa.gov/bio/repo/) | Searchable study and related-record catalog for NASA space-life-science data; GeneLab and ALSDA collections | Omics, physiology, phenotype, behavior, imaging, environmental and hardware records; raw and processed products | Public records can be viewed/downloaded under repository terms. Verify the record's files, release/version, organism, data-use conditions, rights, and publication before reuse. |
| [OSDR / GeneLab data processing overview](https://science.nasa.gov/biological-physical/data/osdr/osdr-data-processing/) | Metadata curation and standardized processing information for selected omics | RNA-seq, single-cell RNA-seq, amplicon, metagenomics, microarrays, methylation sequencing and related outputs | Raw and processed files may both be present. Pipeline outputs are analysis products, not ground truth or clinical labels. |
| [OSDR study OSD-689](https://osdr.nasa.gov/bio/repo/data/studies/OSD-689) | Example human immune research study record discovered in OSDR search on 2026-11-14: "Single-cell analysis identifies conserved features of immune dysfunction in simulated microgravity and spaceflight" | The search record identifies Homo sapiens, transcription profiling, and microgravity simulation among its study metadata; the title/description also references spaceflight samples | This is an example of a research dataset, not a clinical dashboard feed. Confirm sample-level provenance, files, release, and terms in the record before any analysis. The search result alone does not establish a prediction target or reusable license. |
| [NASA Life Sciences Portal](https://nlsp.nasa.gov/explore/) | Current NASA portal for life-sciences information; the legacy LSDA address redirects here | Catalog and records related to life-sciences studies and NASA research | Access and availability can differ by record and collection. Do not assume a historical LSDA record is public or has the same terms as an OSDR record. |
| [NASA Technical Reports Server (NTRS)](https://ntrs.nasa.gov/) | Searchable NASA technical reports, evidence reports, conference material, and publication metadata | Research summaries, methods, reports, study abstracts, and some downloadable documents | NTRS is a research literature/archive source, not a general raw health-data API. Each record indicates dissemination and may have record-specific copyright or reuse status. |
| [Data.nasa.gov](https://data.nasa.gov/) | Metadata catalog describing publicly available NASA datasets and linking to their hosting archives | Catalog metadata and links to data hosted elsewhere | Catalog presence does not mean the underlying files are hosted there or that the catalog entry is a clinical dataset. Follow the source link and its terms. |
| [OSDR on AWS](https://www.nasa.gov/reference/osdr-help-getting-started-with-aws-and-osdr-data/) | NASA's instructions for browsing/copying public OSDR files in the Registry of Open Data on AWS | OSDR file objects by study and version, including large raw/processed study files | NASA documents unsigned public reads for the open bucket and gives OSD-96 as a command example. This establishes access mechanics for public content, not permission to redistribute every file or a blanket license. |

### Example dataset review: OSD-689

The OSDR search result available during this review matched "NASA Twins Study"
because its description mentions the Twins study among related comparison
material. Its title is *Single-cell analysis identifies conserved features
of immune dysfunction in simulated microgravity and spaceflight*. The visible
search metadata identifies human (Homo sapiens) and transcription profiling,
and notes microgravity-simulation conditions. This is a useful candidate for
learning about immune omics and study provenance, not a vitals time series.

Before reuse, a researcher must inspect the full study record and files to
confirm which samples are from flight, analogs, or comparison sources; the
study version and processing pipeline; data dictionaries; subject/sample
relationships; publication; and any terms or restrictions. This research
review did not download, normalize, or analyze OSD-689 files.

NASA's AWS guide uses OSD-96 as an example S3 path and file. The named example
file is a *Drosophila melanogaster* RNA-seq file, so that example must not be
misrepresented as human astronaut health data.

## Access, privacy, and licensing

1. **Check each record and file.** NASA's OSDR terms state that public content
   may be viewed or downloaded, but prohibit submission of classified, CUI,
   sensitive, proprietary, or copyrighted material without proper permission.
   The terms also require submitters to have rights to distribute material.
2. **Do not assume one repository-wide license.** Public availability is not
   itself a Creative Commons or other open license. Record the displayed
   copyright/rights statement, license (if any), attribution instructions,
   version, and any restrictions for every reused file. If rights are missing
   or ambiguous, do not redistribute; ask the repository or rights holder.
3. **Respect human-subject protections.** Do not seek, store, or commit
   identifiable, sensitive, restricted, or controlled human health data in
   the AEGIS repository. Follow the record's consent, access, and data-use
   conditions. Do not attempt re-identification of de-identified material.
4. **Preserve provenance and context.** Capture dataset accession, release or
   version, source archive, publication, organism, sample type, mission or
   analog, treatment/control, collection time, assay, processing method, and
   units where applicable. Keep raw and processed files distinguishable.
5. **Keep publication rights separate from data rights.** A paper may be
   readable while its figures, tables, supplements, or underlying files have
   separate redistribution terms. Cite the work; do not copy figures or
   protected data into project assets without permission.
6. **No live-feed claim.** The catalog and the research records reviewed here
   are not an approved source of live NASA crew telemetry. The current AEGIS
   fixture remains synthetic.

## Scientific suitability for AEGIS

- **Potential educational/research use:** study-level, de-identified, public
  research data may support a clearly scoped offline demonstration after
  record-specific review and team approval.
- **Not suitable as currently documented:** subject-level data are not an
  approved source for the AEGIS live dashboard, clinical labels, universal
  normal ranges, or individual astronaut risk predictions.
- **Generalization limits:** many studies have small cohorts, animal or cell
  models, analog environments, distinct instruments and protocols, and
  mission-specific sampling. These cannot be silently merged into a
  representative astronaut population.
- **No model labels by default:** a dataset's exposed group, assay, or
  observed outcome is not automatically a medically meaningful ground-truth
  label.

## Recommendation

For the current project, cite NASA repositories and studies as research
sources, but keep the operational/demo fixture synthetic. If the team later
selects a public dataset for an offline experiment, write a separate dataset
card first containing its accession/version, exact files, research question,
population/model, license and access review, preprocessing, missingness,
confounders, and restrictions. Obtain appropriate review before any use of
human-subject data.

## Sources checked

- [NASA OSDR overview](https://science.nasa.gov/biological-physical/data/osdr/)
- [OSDR search portal](https://osdr.nasa.gov/bio/repo/)
- [OSDR data processing overview](https://science.nasa.gov/biological-physical/data/osdr/osdr-data-processing/)
- [OSDR terms and conditions](https://science.nasa.gov/reference/osdr-help-terms-and-conditions/)
- [NASA OSDR AWS access guide](https://www.nasa.gov/reference/osdr-help-getting-started-with-aws-and-osdr-data/)
- [NASA Life Sciences Portal](https://nlsp.nasa.gov/explore/)
- [Data.nasa.gov description](https://data.nasa.gov/)
- [OSDR OSD-689 search record](https://osdr.nasa.gov/bio/repo/data/studies/OSD-689)

