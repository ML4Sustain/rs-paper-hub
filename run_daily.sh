#!/usr/bin/env bash
# Daily update script for RS-Paper-Hub
# Usage:
#   bash run_daily.sh          # default: arXiv API
#   bash run_daily.sh --web    # fallback: scrape arXiv HTML (when API is down)
#   bash run_daily.sh --no-push  # run without git push

set -e
cd "$(dirname "$0")"

MODE="api"
NO_PUSH=false
for arg in "$@"; do
  case "$arg" in
    --web)      MODE="web" ;;
    --no-push)  NO_PUSH=true ;;
  esac
done

echo "========== RS-Paper-Hub Daily Update =========="
echo "$(date '+%Y-%m-%d %H:%M:%S')  [mode: $MODE]"
echo ""

# 1. Fetch latest papers (last 7 days)
echo "[1/4] Fetching latest papers..."
if [[ "$MODE" == "web" ]]; then
  python3 main_web.py --update
else
  python3 main.py --update
fi

# 2. Run full pipeline (clean + classify + tag + filter + trends)
echo ""
echo "[2/4] Running pipeline..."
python3 pipeline.py

# 3. Commit and push (if there are changes)
echo ""
echo "[3/4] Checking for changes..."
git add output/ groups/ trends/
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  PAPER_COUNT=$(python3 -c "import json; print(len(json.load(open('output/papers.json'))))")
  VLM_COUNT=$(python3 -c "import json; print(len(json.load(open('output/papers_vlm.json'))))")
  AGENT_COUNT=$(python3 -c "import json; print(len(json.load(open('output/papers_agent.json'))))")
  UAV_COUNT=$(python3 -c "import json; print(len(json.load(open('output/papers_uav.json'))))")
  SAR_COUNT=$(python3 -c "import json; print(len(json.load(open('output/papers_sar.json'))))")
  HYP_COUNT=$(python3 -c "import json; print(len(json.load(open('output/papers_hyp.json'))))")
  git commit -m "chore: daily update ${PAPER_COUNT} papers (${VLM_COUNT} VLM, ${AGENT_COUNT} Agent, ${UAV_COUNT} UAV, ${SAR_COUNT} SAR, ${HYP_COUNT} Hyp/MS)

Updated: $(date -u +'%Y-%m-%d %H:%M UTC')"

  if [[ "$NO_PUSH" == "true" ]]; then
    echo "Skipping push (--no-push)."
  else
    echo "Pushing to remote..."
    git push
  fi
fi

# 4. Summary
echo ""
echo "[4/4] Done!"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
