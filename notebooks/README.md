# eDNA Pipeline — Interactive Notebooks

These notebooks are interactive learning companions for the eDNA metabarcoding pipeline. They are designed for Yaw Baah — biologist and pipeline author — to explore what the code does step by step, with biological context and runnable examples. Every cell runs without internet access and without a BLAST+ installation. Synthetic BLAST XML files are generated inline where needed, so you can follow each concept from raw sequence data through to species identification tables and biodiversity metrics.

## Notebooks

| Notebook | What it covers | Prerequisites |
|---|---|---|
| `01_BLAST_and_Species_Parsing.ipynb` | How BLAST works (seed→extend→score); the 4 key metrics; running `parse_all_results` on synthetic data; how `_extract_species` handles messy BLAST titles (uncultured, cf., hybrid, metagenome); LCA taxonomy resolution with `resolve_taxonomy`; Shannon H' and Pielou J' diversity metrics | Python ≥3.10, requirements.txt installed |
| `02_Local_BLAST_and_Databases.ipynb` | Why local BLAST matters for reproducibility; BLAST+ database file types (.nsq/.nin/.nhr/.nal); checking installation with `shutil.which`; the XML caching system; database selection guide for UK freshwater eDNA (nt vs 16S vs 18S vs SILVA); full `--local` command walkthrough; `db_version.json` as a regulatory audit trail | Notebook 01, Python ≥3.10, requirements.txt installed |

## How to run

### Option 1 — GitHub Codespaces

1. Open the repository on GitHub and click **Code → Codespaces → Create codespace on main**
2. Once the environment loads, open a terminal and run:
   ```
   pip install -r requirements.txt
   jupyter notebook notebooks/
   ```
3. A browser tab will open with the Jupyter interface. Click a notebook to open it, then use **Run → Run All Cells** or step through cells with **Shift+Enter**

### Option 2 — Run locally

1. Clone the repository and install dependencies:
   ```
   pip install -r requirements.txt
   pip install jupyter
   ```
2. Launch Jupyter from the **project root** (not from inside `notebooks/`):
   ```
   jupyter notebook
   ```
3. In the browser, navigate to `notebooks/` and open a file
4. Run cells top to bottom with **Shift+Enter**, or use **Kernel → Restart & Run All**

> **Important:** Always launch Jupyter from the project root directory. The notebooks use `Path.cwd().parent` to locate the project root, which assumes they are one level inside it.
