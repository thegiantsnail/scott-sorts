#!/usr/bin/env bash
# Reproduce all results from "The Scott Topology of Sorting Algorithms"
# Usage: ./run_all.sh

set -euo pipefail

echo "=== 1. CFG/DFG Analysis of Sorting Algorithms ==="
python3 src/sort_analysis.py

echo ""
echo "=== 2. Scott & Lawson Topology Computation ==="
python3 src/scott_topology.py

echo ""
echo "=== 3. Endomorphism Classification ==="
python3 src/endomorphism_analysis.py

echo ""
echo "=== 4. Efficiency Ranking & Symmetry Classes ==="
python3 src/efficiency_symmetry.py

echo ""
echo "=== All analyses complete. ==="
