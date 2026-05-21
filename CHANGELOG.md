# Changelog

All notable changes to this project are documented here.

---

## [Unreleased] — 2026-05-21

### Overview

This release addresses seven parser bugs that produced biologically incorrect
species names and corrupted biodiversity metrics, and adds three new
classification capabilities that make the pipeline meaningful for real
environmental samples including uncultured and low-identity sequences.

---

### Bug Fixes

#### `src/parser.py` — `_extract_species`

**1. `cf.` / `aff.` qualifiers no longer corrupt species names**

BLAST titles such as `Alternaria cf. alternata` previously returned
`"Alternaria cf"` because `"cf"` (after stripping the period) passed the
lowercase + alphabetic epithet checks. The fix introduces a `_SKIP_QUALIFIERS`
set (`cf`, `aff`, `var`, `subsp`, `ssp`, `f`, `fo`, `nov`, `sp`, `x`) whose
members are stepped over when scanning for the species epithet.

- Before: `"Alternaria cf. alternata"` → `"Alternaria cf"` ❌
- After:  `"Alternaria cf. alternata"` → `"Alternaria alternata"` ✓

**2. Multi-hit concatenated titles use only the first database record**

`alignment.title` in BLAST XML concatenates multiple matching database
entries with `>`. The full string was previously tokenised, mixing species
from different entries. The fix splits on `>` and operates only on the first
record.

**3. Descriptor words (`clone`, `isolate`, `strain`, `voucher` …) no longer
become species epithets**

Without a `_STOP_WORDS` set, words like `"clone"` and `"isolate"` (lowercase,
alphabetic) were returned as species epithets. Example: `"Betula clone BET001"`
would return `"Betula clone"`. The fix adds `_STOP_WORDS` — encountering one of
these while scanning for an epithet terminates the search and falls back to
`"Genus sp."`.

**4. Hybrid `×` notation no longer breaks parsing**

The Unicode multiplication sign `×` caused `isalpha()` to fail on surrounding
tokens, skipping hybrid names entirely. The fix replaces `×` with a space
before tokenising. Lowercase `x` hybrid notation (`Betula x pubescens`) is
handled by including `"x"` in `_SKIP_QUALIFIERS`.

**5. Genus-only resolution uses `"Genus sp."` not bare `"Genus"`**

When a genus was identified but no valid epithet followed, the bare genus
name was returned (e.g. `"Betula"`). This is not a valid taxonomic name.
The fix returns `"Genus sp."`, which is the correct International Code of
Nomenclature notation for an unresolved species within a known genus.

#### `src/parser.py` — `parse_blast_xml`

**6. Coverage percentage clamped to 100 %**

`hsp.align_length / query_length * 100` can exceed 100 when the subject
sequence contains insertions relative to the query. The fix applies
`min(..., 100.0)`.

**7. Best HSP selected explicitly by bit score**

`alignment.hsps[0]` assumed BLAST XML delivers HSPs in descending score order,
which is not guaranteed. The fix uses `max(alignment.hsps, key=lambda h: h.bits)`.

**8. Zero-length alignment guard**

No check existed before `hsp.identities / hsp.align_length`. A degenerate
record with `align_length == 0` would raise `ZeroDivisionError`, silently
caught by the outer exception handler, dropping all hits from that file. The
fix adds an explicit guard that logs a warning and skips only the affected
alignment.

#### `src/summarise.py` — `calculate_diversity`

**9. `"unclassified"` excluded from diversity metrics**

Previously `"unclassified"` was counted as a real taxon. A dataset with five
birch sequences and three uncultured reads would report Shannon H′ and Pielou
J′ values inflated by a phantom sixth species. The fix separates unclassified
hits before any metric computation and reports their count in a new
`unclassified_queries` field.

---

### New Features

#### Uncultured genus rescue (`src/parser.py`)

Many NCBI environmental entries carry the prefix `"uncultured"` but contain
a valid genus name — for example `"uncultured Chlorella sp. clone ENV45"`.
The previous code discarded all such entries as `"unclassified"`. The new
`_STOP_WORDS` mechanism means that after skipping `"uncultured"` (blocked by
`_NON_SPECIFIC_TERMS`), the genus `"Chlorella"` is found normally and the
result is `"Chlorella sp."`. Genuine unknowns such as `"uncultured fungus clone
ABC"` still return `"unclassified"` because `"fungus"` starts with a lowercase
letter and cannot be treated as a genus.

This is the most impactful improvement for pond and soil eDNA samples where
a large fraction of sequences match environmental entries in NCBI.

#### LCA (Lowest Common Ancestor) classification (`src/summarise.py`)

A new `resolve_taxonomy()` function examines all BLAST hits for each query
sequence together and assigns the deepest taxonomic level that the evidence
supports:

| Top-hit identity | LCA action |
|---|---|
| ≥ 97 % | Accept species name from rank-1 hit |
| 90–96 % | Check hits within 2 % of top score; if all agree on genus → `"Genus sp."` |
| < 90 % | Check all hits; if all agree on genus → `"Genus sp."`; if genera conflict → `"unclassified"` |

This prevents the pipeline from reporting `"Daphnia pulex"` when the 93 %
identity match could equally be `Daphnia magna` or `Daphnia longispina`.

The raw BLAST-extracted name is preserved in the `species` column for
reference. The `resolved_species` column contains the LCA-corrected name
used in diversity calculations.

#### Confidence flag column (`src/summarise.py`)

`build_hit_table()` now adds a `confidence_flag` column to `blast_hit_table.csv`:

| Value | Identity threshold | Meaning |
|---|---|---|
| `high`   | ≥ 97 % | Species-level assignment reliable |
| `medium` | 90–96 % | Genus-level reliable; species uncertain |
| `low`    | < 90 % | Too divergent for confident placement |

---

### Mock run

A new `mock_run.py` script demonstrates the pipeline end-to-end without
requiring NCBI network access. It generates synthetic BLAST XML for eight
representative UK freshwater pond organisms and exercises all three new
classification features:

```
python mock_run.py
```

Organisms included: *Chlorella vulgaris*, *Microcystis aeruginosa* (×2,
representing a bloom), uncultured *Chlamydomonas* sp. (uncultured rescue),
*Daphnia* spp. (medium LCA), *Chironomus* spp. (low LCA, genus consensus),
mixed diatoms (low LCA, genus conflict → unclassified), *Phragmites australis*.

---

### Test coverage

`tests/test_parser.py` expanded from 11 to 25 test cases. New cases cover:

- `cf.` / `aff.` qualifier skipping
- `var.` / `subsp.` qualifier skipping
- Multi-hit title isolation
- Uncultured genus rescue
- Uncultured + non-specific bracket → `"unclassified"`
- Metagenome title → `"unclassified"`
- Hybrid `×` and lowercase `x` notation
- Genus-only sp. suffix
- `sp.` abbreviation in title
- Coverage capped at 100 %
- LCA: unclassified excluded from richness
- LCA: unclassified count reported separately
- `confidence_flag` column presence and values

---

### Files changed

| File | Change |
|---|---|
| `src/parser.py` | Bugs 1–8, uncultured rescue, `_STOP_WORDS` |
| `src/summarise.py` | Bug 9, LCA `resolve_taxonomy()`, confidence flag |
| `tests/test_parser.py` | 14 new test cases |
| `mock_run.py` | New — offline demonstration script |
| `CHANGELOG.md` | New — this file |
