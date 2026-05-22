#!/bin/bash
# eDNA pipeline devcontainer setup
set -e

echo "==> Installing BLAST+ binaries..."
sudo apt-get update -qq
sudo apt-get install -y -qq ncbi-blast+ ncbi-blast+-legacy

echo "==> Installing Python dependencies..."
pip install --quiet -r requirements.txt

echo "==> Installing development tools..."
pip install --quiet pytest pytest-cov black pylint

echo "==> Verifying BLAST+ installation..."
blastn -version

echo "==> Running test suite..."
python -m pytest tests/ -q

echo ""
echo "============================================"
echo "  Environment ready."
echo "  BLAST+:  $(blastn -version 2>&1 | head -1)"
echo "  Python:  $(python --version)"
echo ""
echo "  Quick start:"
echo "    python mock_run.py          — offline pond demo"
echo "    python pipeline.py --help   — full CLI options"
echo "============================================"
