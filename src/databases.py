"""
src/databases.py — Curated database registry for the eDNA pipeline.

Provides a central registry of supported BLAST databases, their associated
gene markers, target organisms, and download sources.  Used by the pipeline
to auto-select the correct database when --marker is supplied, and by
scripts/setup_db.py to guide downloads.

Phase 4 of the eDNA metabarcoding pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

__all__ = [
    "DatabaseInfo",
    "DATABASE_REGISTRY",
    "get_database_info",
    "recommend_database",
    "list_databases",
]


@dataclass
class DatabaseInfo:
    """Metadata for a single BLAST reference database."""

    name: str
    """Short identifier used as a key in DATABASE_REGISTRY and CLI flag values."""

    display_name: str
    """Human-readable name printed in logs and reports."""

    markers: List[str]
    """Gene markers this database is appropriate for (e.g. ['16S', '18S'])."""

    organisms: str
    """Plain-English description of the target taxonomic group."""

    source: str
    """Data provider: 'ncbi' | 'silva' | 'bold' | 'midori' | 'pr2'."""

    download_url: str
    """Primary download URL or landing page for this database."""

    approx_size_gb: float
    """Approximate download size in gigabytes (uncompressed BLAST files)."""

    description: str
    """One-sentence description for display in --list output and the PDF report."""

    ncbi_name: Optional[str] = None
    """NCBI update_blastdb.pl identifier — set only for NCBI-hosted databases."""

    recommended_for: List[str] = field(default_factory=list)
    """Survey types this database is recommended for."""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DATABASE_REGISTRY: dict[str, DatabaseInfo] = {

    "silva_ssu": DatabaseInfo(
        name="silva_ssu",
        display_name="SILVA 138.2 SSU",
        markers=["16S", "18S"],
        organisms="Bacteria, archaea, eukaryotes",
        source="silva",
        download_url=(
            "https://www.arb-silva.de/fileadmin/silva_databases/"
            "release_138_2/Exports/"
            "SILVA_138.2_SSURef_NR99_tax_silva.fasta.gz"
        ),
        approx_size_gb=10.0,
        description=(
            "Curated small-subunit rRNA. Standard for bacterial and "
            "eukaryote eDNA community surveys."
        ),
        recommended_for=["bacterial water quality", "eukaryote community survey"],
    ),

    "bold": DatabaseInfo(
        name="bold",
        display_name="BOLD (Barcode of Life Database)",
        markers=["COI"],
        organisms="Animals — invertebrates, fish, birds, mammals",
        source="bold",
        download_url="https://www.boldsystems.org/index.php/datapackages",
        approx_size_gb=3.0,
        description=(
            "Curated COI barcode sequences for >200,000 animal species. "
            "Primary reference for invertebrate and fish identification."
        ),
        recommended_for=["macroinvertebrate survey", "fish community survey"],
    ),

    "midori2": DatabaseInfo(
        name="midori2",
        display_name="MIDORI2",
        markers=["12S", "COI", "16S"],
        organisms="Vertebrates — fish, amphibians, reptiles, mammals, birds",
        source="midori",
        download_url="https://www.reference-midori.info/download.php",
        approx_size_gb=2.0,
        description=(
            "Curated vertebrate mitochondrial genes (12S, COI, 16S). "
            "Recommended for freshwater fish, GCN, and amphibian eDNA surveys."
        ),
        recommended_for=[
            "freshwater fish survey",
            "great crested newt survey",
            "amphibian survey",
            "vertebrate eDNA",
        ],
    ),

    "its_refseq_fungi": DatabaseInfo(
        name="its_refseq_fungi",
        display_name="ITS_RefSeq_Fungi",
        markers=["ITS", "ITS1", "ITS2"],
        organisms="Fungi",
        source="ncbi",
        download_url="https://ftp.ncbi.nlm.nih.gov/blast/db/",
        approx_size_gb=1.0,
        description=(
            "NCBI RefSeq ITS1/ITS2 sequences for fungi. "
            "Standard reference for mycological eDNA surveys."
        ),
        ncbi_name="ITS_RefSeq_Fungi",
        recommended_for=["fungal community survey", "mycology"],
    ),

    "16s_rrna": DatabaseInfo(
        name="16s_rrna",
        display_name="16S ribosomal RNA (NCBI)",
        markers=["16S"],
        organisms="Bacteria, archaea",
        source="ncbi",
        download_url="https://ftp.ncbi.nlm.nih.gov/blast/db/",
        approx_size_gb=1.0,
        description=(
            "NCBI curated 16S rRNA sequences. "
            "Good for targeted bacterial surveys; SILVA SSU preferred for "
            "comprehensive environmental surveys."
        ),
        ncbi_name="16S_ribosomal_RNA",
        recommended_for=["targeted bacterial survey"],
    ),

    "pr2": DatabaseInfo(
        name="pr2",
        display_name="PR2 (Protist Ribosomal Reference)",
        markers=["18S"],
        organisms="Protists, algae, phytoplankton",
        source="pr2",
        download_url=(
            "https://github.com/pr2database/pr2database/releases/latest"
        ),
        approx_size_gb=0.5,
        description=(
            "Curated 18S rRNA database for protists and algae. "
            "Use for phytoplankton or micro-eukaryote eDNA surveys."
        ),
        recommended_for=["phytoplankton survey", "protist survey", "algae survey"],
    ),

    "nt": DatabaseInfo(
        name="nt",
        display_name="NCBI Nucleotide (nt)",
        markers=["16S", "18S", "COI", "ITS", "ITS1", "ITS2", "12S"],
        organisms="All organisms (general purpose)",
        source="ncbi",
        download_url="https://ftp.ncbi.nlm.nih.gov/blast/db/",
        approx_size_gb=300.0,
        description=(
            "General-purpose nucleotide collection (GenBank/EMBL/DDBJ). "
            "Use only when no curated database covers your marker — "
            "slow and noisier than targeted databases."
        ),
        ncbi_name="nt",
        recommended_for=["general purpose", "novel marker"],
    ),
}

# ---------------------------------------------------------------------------
# Marker → recommended database
# ---------------------------------------------------------------------------

_MARKER_TO_DB: dict[str, str] = {
    "16S":  "silva_ssu",
    "18S":  "silva_ssu",
    "COI":  "bold",
    "12S":  "midori2",
    "ITS":  "its_refseq_fungi",
    "ITS1": "its_refseq_fungi",
    "ITS2": "its_refseq_fungi",
}

_VALID_MARKERS = sorted(_MARKER_TO_DB.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_database_info(name: str) -> DatabaseInfo:
    """Return DatabaseInfo for *name* (case-insensitive).

    Raises
    ------
    KeyError
        If *name* is not in DATABASE_REGISTRY.
    """
    key = name.lower().replace("-", "_").replace(" ", "_")
    # Try exact key first, then case-folded lookup
    if key in DATABASE_REGISTRY:
        return DATABASE_REGISTRY[key]
    # Partial match against registered names
    for db_key, db_info in DATABASE_REGISTRY.items():
        if db_key == key or db_info.ncbi_name == name:
            return db_info
    raise KeyError(
        f"Unknown database: '{name}'. "
        f"Valid options: {sorted(DATABASE_REGISTRY.keys())}"
    )


def recommend_database(marker: str) -> DatabaseInfo:
    """Return the recommended DatabaseInfo for *marker*.

    Parameters
    ----------
    marker:
        Gene marker string, e.g. '16S', 'COI', 'ITS', '12S', '18S'.
        Case-insensitive.

    Returns
    -------
    DatabaseInfo
        The recommended database for this marker.

    Raises
    ------
    ValueError
        If *marker* is not a recognised gene marker.
    """
    key = marker.upper().strip()
    if key not in _MARKER_TO_DB:
        raise ValueError(
            f"Unknown marker: '{marker}'. "
            f"Supported markers: {_VALID_MARKERS}. "
            f"For unsupported markers use --db-path directly with the 'nt' database."
        )
    return DATABASE_REGISTRY[_MARKER_TO_DB[key]]


def list_databases() -> List[DatabaseInfo]:
    """Return all registered databases sorted by name."""
    return sorted(DATABASE_REGISTRY.values(), key=lambda d: d.name)
