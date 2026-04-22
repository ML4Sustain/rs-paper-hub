#!/usr/bin/env bash
# Daily update script for RS-Paper-Hub
# Usage: bash run_daily.sh

set -e
cd "$(dirname "$0")"

echo "========== RS-Paper-Hub Daily Update =========="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Fetch latest papers (last 7 days)
echo "[1/3] Fetching latest papers..."
python3 main.py --update

# 2. Run full pipeline (clean + classify + tag + filter + trends)
echo ""
echo "[2/3] Running pipeline..."
python3 pipeline.py

# 3. Summary
echo ""
echo "[3/3] Done!"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
