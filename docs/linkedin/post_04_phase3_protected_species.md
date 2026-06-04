# LinkedIn Post 04 — Phase 3: Protected Species Detection

*Angle: Legal stakes — the pipeline now flags species with criminal consequences*
*Status: DRAFT*

---

If an eDNA survey detects great crested newt DNA and nobody flags it, that's not a data problem. That's a legal problem.

Disturbing a great crested newt, its eggs, or its habitat is a criminal offence under the Habitats Regulations 2017. The same applies to European Protected Species across the board — otters, white-clawed crayfish, Atlantic salmon, water voles. These aren't edge cases. They come up regularly in freshwater eDNA surveys, and missing one because your pipeline didn't check is exactly the kind of thing that ends a project or a professional reputation.

Phase 3 adds protected species detection to the pipeline.

`src/protected.py` holds a list of 20 UK aquatic and riparian species drawn from four legislative frameworks:

- **EPS** — European Protected Species (Habitats Regulations 2017)
- **WCA Schedule 5** — Wildlife & Countryside Act 1981, protected animals
- **WCA Schedule 6** — prohibited methods of taking/killing
- **Section 41** — Species of Principal Importance (NERC Act 2006)

Every species identification that comes back from BLAST is checked against this list. The system flags two alert levels:

- **CONFIRMED** — species-level match at ≥97% identity. The pipeline detected DNA consistent with that protected species.
- **POSSIBLE** — genus-level match, identity 90–96%. The genus contains a protected species. Needs ecological review.

When confirmed alerts exist, the PDF report opens with a red banner — before the executive summary, before the species table. It lists the species, its common name, the legislation it's protected under, and the query IDs from the FASTA file. Every alert section closes with the same disclaimer: *these detections require review by a qualified ecologist before regulatory submission.*

The pipeline doesn't make the regulatory decision. That's not its job. Its job is to make sure nothing slips past unnoticed.

50 unit tests passing. Code on GitHub.

Code: github.com/ybaah-biotech/eDNA-sequence-analysis

#eDNA #ProtectedSpecies #EnvironmentalLaw #Bioinformatics #Python #GreatCrestedNewt
