"""
Phase 3 – Protected Species Cross-Reference
============================================

This module cross-references species identified by BLAST against a curated
dictionary of UK-protected aquatic and freshwater species, returning structured
alerts for use in ecological survey reports.

Legislation covered
-------------------
EPS   – European Protected Species under the Conservation of Habitats and
        Species Regulations 2017 (Habitats Regulations).  Disturbance,
        destruction of habitat, and killing/taking individuals are criminal
        offences without a licence.

WCA   – Wildlife and Countryside Act 1981 (as amended).
        Schedule 5 species are protected against intentional killing, injuring,
        or taking.  Schedule 6 species may not be taken or killed by certain
        methods.

S41   – Section 41 of the Natural Environment and Rural Communities (NERC)
        Act 2006 (England).  Lists species of principal importance for
        conserving biodiversity in England; public bodies must have regard to
        their conservation.

BAP   – UK Biodiversity Action Plan species (legacy designation retained for
        reference; largely superseded by S41 and equivalent devolved lists).

IMPORTANT
---------
This list has been assembled from publicly available UK legislation and
conservation guidance.  It does not constitute legal advice.  It MUST be
reviewed and verified by a suitably qualified ecologist (SQE) before use in
any professional survey report or planning application.  Species records,
protected-site boundaries, and licence requirements change over time; the
user is responsible for ensuring this list is current and appropriate for
the survey location and target taxa.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protected species reference dictionary
# Keys are binomial names (Genus species) in title case.
# ---------------------------------------------------------------------------

PROTECTED_UK_SPECIES: Dict[str, Dict[str, Any]] = {
    "Triturus cristatus": {
        "common_name": "Great Crested Newt",
        "legislation": ["EPS", "WCA Schedule 5"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; any disturbance to individuals or "
            "destruction of breeding habitat requires a Habitats Regulations licence."
        ),
    },
    "Lutra lutra": {
        "common_name": "Otter",
        "legislation": ["EPS", "WCA Schedule 5"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; watercourse works near holts require "
            "an otter survey by an SQE and potentially a Habitats Regulations licence."
        ),
    },
    "Austropotamobius pallipes": {
        "common_name": "White-clawed Crayfish",
        "legislation": ["EPS", "WCA Schedule 5"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; handling, translocation, or habitat "
            "modification requires a Habitats Regulations licence."
        ),
    },
    "Margaritifera margaritifera": {
        "common_name": "Freshwater Pearl Mussel",
        "legislation": ["EPS", "WCA Schedule 5"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; one of the most threatened freshwater "
            "invertebrates in the UK — any in-stream works require a licence."
        ),
    },
    "Lampetra planeri": {
        "common_name": "Brook Lamprey",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; disturbance to spawning gravels or "
            "juveniles in silt requires a Habitats Regulations licence."
        ),
    },
    "Lampetra fluviatilis": {
        "common_name": "River Lamprey",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; migratory — barrier removal consents "
            "and in-river works must consider potential impacts."
        ),
    },
    "Petromyzon marinus": {
        "common_name": "Sea Lamprey",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; the largest UK lamprey — spawning "
            "habitat disturbance is a criminal offence without a licence."
        ),
    },
    "Arvicola amphibius": {
        "common_name": "Water Vole",
        "legislation": ["WCA Schedule 5"],
        "protection_level": "WCA",
        "alert_level": "HIGH",
        "survey_note": (
            "Protected under WCA Schedule 5; riparian habitat modification or "
            "bankside works require a water vole survey and mitigation strategy."
        ),
    },
    "Luronium natans": {
        "common_name": "Floating Water-plantain",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species plant; any works affecting populations "
            "or seed banks in water bodies or ditches require a licence."
        ),
    },
    "Salmo salar": {
        "common_name": "Atlantic Salmon",
        "legislation": ["WCA Schedule 5", "S41"],
        "protection_level": "WCA",
        "alert_level": "MEDIUM",
        "survey_note": (
            "Listed under WCA and S41; in-river works during spawning (Oct–Jan) "
            "should be avoided and may require consent from the Environment Agency."
        ),
    },
    "Anguilla anguilla": {
        "common_name": "European Eel",
        "legislation": ["S41"],
        "protection_level": "S41",
        "alert_level": "MEDIUM",
        "survey_note": (
            "Listed under S41 as a species of principal importance; eel passes "
            "and barrier management should be considered in any impoundment project."
        ),
    },
    "Alosa alosa": {
        "common_name": "Allis Shad",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; spawning migrations require river "
            "access — impoundments and major abstractions need Habitats Regulations "
            "assessment."
        ),
    },
    "Alosa fallax": {
        "common_name": "Twaite Shad",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; migratory shad with designated SAC "
            "populations — any works near breeding rivers require HRA screening."
        ),
    },
    "Coregonus lavaretus": {
        "common_name": "Vendace",
        "legislation": ["WCA Schedule 5"],
        "protection_level": "WCA",
        "alert_level": "HIGH",
        "survey_note": (
            "Protected under WCA Schedule 5; one of the UK's rarest freshwater "
            "fish, restricted to a handful of lakes — any disturbance is a "
            "serious legal concern."
        ),
    },
    "Thymallus thymallus": {
        "common_name": "Grayling",
        "legislation": ["S41"],
        "protection_level": "S41",
        "alert_level": "MEDIUM",
        "survey_note": (
            "Listed under S41; a sensitive indicator of clean, fast-flowing "
            "water — in-river works should avoid the spawning season (Mar–May)."
        ),
    },
    "Neomys fodiens": {
        "common_name": "Water Shrew",
        "legislation": ["WCA Schedule 6"],
        "protection_level": "WCA",
        "alert_level": "LOW",
        "survey_note": (
            "Protected under WCA Schedule 6 against taking by certain methods; "
            "riparian habitat should be retained where possible."
        ),
    },
    "Myotis daubentonii": {
        "common_name": "Daubenton's Bat",
        "legislation": ["EPS", "WCA Schedule 5"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; frequently forages over water — tree "
            "and bridge works near roosts or commuting routes require a bat survey "
            "and potentially a Habitats Regulations licence."
        ),
    },
    "Hydrophilus piceus": {
        "common_name": "Great Silver Water Beetle",
        "legislation": ["WCA Schedule 5"],
        "protection_level": "WCA",
        "alert_level": "MEDIUM",
        "survey_note": (
            "Protected under WCA Schedule 5; associated with large ponds and "
            "slow rivers with emergent vegetation — habitat loss triggers "
            "legal protection obligations."
        ),
    },
    "Coenagrion mercuriale": {
        "common_name": "Southern Damselfly",
        "legislation": ["EPS", "WCA Schedule 5"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species; strongly associated with clean, "
            "shallow chalk streams — any modification of breeding habitat requires "
            "a Habitats Regulations licence."
        ),
    },
    "Vertigo moulinsiana": {
        "common_name": "Desmoulin's Whorl Snail",
        "legislation": ["EPS"],
        "protection_level": "EPS",
        "alert_level": "HIGH",
        "survey_note": (
            "A European Protected Species gastropod found in wet, tall-herb fen "
            "and riparian marshes — ditch clearance or drainage must be assessed "
            "for likely significant effect."
        ),
    },
}

# ---------------------------------------------------------------------------
# Automatically build a genus-level lookup from the species dictionary above.
# Maps each genus string to the list of full species names it contains.
# ---------------------------------------------------------------------------

PROTECTED_GENERA: Dict[str, List[str]] = {}
for _species_name in PROTECTED_UK_SPECIES:
    _genus = _species_name.split()[0]
    PROTECTED_GENERA.setdefault(_genus, []).append(_species_name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_protected(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cross-reference BLAST results against the UK protected species list.

    Operates on the ``resolved_species`` column produced by Phase 2
    (``summarise.resolve_taxonomy``).  Falls back to the raw ``species``
    column if ``resolved_species`` is absent.

    Only hit_rank == 1 rows are evaluated; all other rows receive ``None``
    for both new columns.

    Parameters
    ----------
    df : pd.DataFrame
        Hit table from ``summarise.build_hit_table``.  Must contain at least
        the columns ``hit_rank``, ``query_id``, and either ``resolved_species``
        or ``species``.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with two additional columns:

        protected_flag : str or None
            ``"CONFIRMED"`` – exact (case-insensitive) match to a key in
            ``PROTECTED_UK_SPECIES``.
            ``"POSSIBLE"``  – the name ends in `` sp.`` and the genus is
            present in ``PROTECTED_GENERA`` (genus-level detection).
            ``None``        – no protected species match found.

        protection_info : dict or None
            For ``"CONFIRMED"`` rows: the full entry from
            ``PROTECTED_UK_SPECIES`` (common_name, legislation,
            protection_level, alert_level, survey_note).
            For ``"POSSIBLE"`` rows: ``None`` (species not confirmed).
            For all other rows: ``None``.
    """
    df = df.copy()

    species_col = "resolved_species" if "resolved_species" in df.columns else "species"

    # Build a lower-case lookup once for O(1) matching.
    _lower_lookup: Dict[str, str] = {k.lower(): k for k in PROTECTED_UK_SPECIES}

    def _classify(row: pd.Series):
        if row["hit_rank"] != 1:
            return None, None

        name: str = str(row.get(species_col, "") or "")
        name_stripped = name.strip()

        if not name_stripped or name_stripped.lower() == "unclassified":
            return None, None

        # Exact match (case-insensitive)
        canonical = _lower_lookup.get(name_stripped.lower())
        if canonical is not None:
            return "CONFIRMED", dict(PROTECTED_UK_SPECIES[canonical])

        # Genus-level match for "Genus sp." names
        if name_stripped.endswith(" sp."):
            genus = name_stripped[:-4].strip()
            if genus in PROTECTED_GENERA:
                return "POSSIBLE", None

        return None, None

    flags = df.apply(_classify, axis=1, result_type="expand")
    df["protected_flag"] = flags[0]
    df["protection_info"] = flags[1]

    return df


def get_alerts(df: pd.DataFrame) -> dict:
    """
    Summarise protected species detections from a flagged hit table.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``check_protected`` — must contain ``protected_flag``,
        ``protection_info``, and ``query_id`` columns.

    Returns
    -------
    dict with keys:

    has_alerts : bool
        ``True`` if any confirmed or possible protected species were detected.

    confirmed : list of dict
        One entry per unique confirmed species, containing:
        ``species``, ``common_name``, ``legislation``, ``protection_level``,
        ``alert_level``, ``survey_note``, ``query_ids``.

    possible : list of dict
        One entry per unique genus with a possible (sp.-level) match,
        containing: ``genus``, ``protected_species_in_genus``, ``query_ids``.

    highest_alert_level : "HIGH" | "MEDIUM" | "LOW" | None
        The most severe alert level present across all confirmed detections.
        ``None`` when there are no confirmed detections.
    """
    _alert_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

    species_col = "resolved_species" if "resolved_species" in df.columns else "species"

    confirmed_map: Dict[str, Dict[str, Any]] = {}
    possible_map: Dict[str, List[str]] = {}

    for _, row in df.iterrows():
        flag = row.get("protected_flag")
        query_id = row.get("query_id", "unknown")

        if flag == "CONFIRMED":
            info = row.get("protection_info") or {}
            # Determine canonical name from the row's species column
            name: str = str(row.get(species_col, "") or "")
            # Match back to canonical key
            canonical = next(
                (k for k in PROTECTED_UK_SPECIES if k.lower() == name.strip().lower()),
                name.strip(),
            )
            if canonical not in confirmed_map:
                confirmed_map[canonical] = {
                    "species": canonical,
                    "common_name": info.get("common_name", ""),
                    "legislation": list(info.get("legislation", [])),
                    "protection_level": info.get("protection_level", ""),
                    "alert_level": info.get("alert_level", ""),
                    "survey_note": info.get("survey_note", ""),
                    "query_ids": [],
                }
            confirmed_map[canonical]["query_ids"].append(query_id)

        elif flag == "POSSIBLE":
            name = str(row.get(species_col, "") or "")
            genus = name.strip()[:-4] if name.strip().endswith(" sp.") else name.strip()
            if genus not in possible_map:
                possible_map[genus] = []
            possible_map[genus].append(query_id)

    confirmed_list = list(confirmed_map.values())

    possible_list = [
        {
            "genus": genus,
            "protected_species_in_genus": list(PROTECTED_GENERA.get(genus, [])),
            "query_ids": query_ids,
        }
        for genus, query_ids in possible_map.items()
    ]

    # Determine highest alert level from confirmed detections only
    highest: Optional[str] = None
    for entry in confirmed_list:
        level = entry.get("alert_level")
        if level and (highest is None or _alert_rank.get(level, 0) > _alert_rank.get(highest, 0)):
            highest = level

    return {
        "has_alerts": bool(confirmed_list or possible_list),
        "confirmed": confirmed_list,
        "possible": possible_list,
        "highest_alert_level": highest,
    }
