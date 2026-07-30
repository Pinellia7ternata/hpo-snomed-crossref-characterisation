# Curated HPO-SNOMED CT cross-reference characterisation

Citable research artifact accompanying the manuscript
**"Complementary Ontological Design of SNOMED CT and the Human Phenotype Ontology:
Modeling Patterns, Reasoning Workflows, and Mapping."**

## Contents

| File | Description |
|------|-------------|
| `six_dimension_matrix.csv` | The six-dimension comparison framework (SNOMED CT vs HPO) used throughout the manuscript. |
| `hpo_snomed_crossrefs.csv` | The full set of 4594 curated HPO->SNOMED CT cross-references extracted from the public HPO release, with inferred mapping cardinality and information-loss flags. |
| `summary_statistics.json` | Aggregate statistics and the chi-square test reported in Section 3.7 of the manuscript. |
| `analyze_hpo_snomed.py` | Self-contained script that regenerates `hpo_snomed_crossrefs.csv` and `summary_statistics.json` from a fresh `hp.obo`. |

## Key results (release analysed)

- Curated cross-references: **4594** (3437 distinct HPO terms, 4369 distinct SNOMED CT identifiers)
- Mapping cardinality: exact **53.4%**, narrow **37.1%**, broad **9.4%**
- Granularity / coverage mismatch: **46.6%**
- Clinical-modifier signal present: **1.9%**
- Cardinality x modifier-loss independence: chi-square = 1.18, p = 0.277 (not significant)

## Reproduce

```bash
# 1. download the HPO release used
curl -L -o hp.obo https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.obo
# 2. regenerate the CSV + JSON
python analyze_hpo_snomed.py
```

## Scope and caveats

These cross-references are expert-asserted equivalences and near-equivalences maintained by the
HPO team. They characterise the **curated interface** between HPO and SNOMED CT; they are **not** a
random sample of the full SNOMED CT Clinical finding branch and are **not** a coverage, recall, or
precision benchmark. All counts are release-dependent.

## Data sources and licensing

- HPO (`hp.obo`): obophenotype/human-phenotype-ontology, released under CC BY 4.0.
- SNOMED CT identifiers appear only as coded references; no SNOMED CT content is redistributed here.
  Use of SNOMED CT requires an appropriate SNOMED International / member licence.

## How to cite

Cite the manuscript above and this artifact by its DOI once minted (see below).

---

## How to deposit and mint a DOI (do this before submission / on acceptance)

**Zenodo (recommended, GitHub-integrated):**
1. Create a public GitHub repository and push this `zenodo_resource/` folder.
2. Sign in to https://zenodo.org with your ORCID/GitHub, open *Account -> GitHub*, and flip the repo switch **On**.
3. In GitHub, create a release (e.g., `v1.0`). Zenodo automatically archives it and mints a DOI.
4. Copy the DOI badge; replace `10.5281/zenodo.XXXXXXX` in the manuscript Data availability statement.

**Zenodo (manual upload, no GitHub):**
1. https://zenodo.org -> *New upload* -> drag in all files from this folder.
2. Upload type = *Dataset*; add authors, title, description (paste the top of this README), licence (CC BY 4.0).
3. *Save* then *Publish* -> a DOI is minted immediately (use *Reserve DOI* first if you need it before publishing).

**OSF mirror (optional):**
1. https://osf.io -> *Create new project* -> upload the same files.
2. In *Settings*, *Create DOI*; link the OSF and Zenodo records to each other in their descriptions.

CITATION.cff in this folder is pre-filled; update the DOI field after minting.
