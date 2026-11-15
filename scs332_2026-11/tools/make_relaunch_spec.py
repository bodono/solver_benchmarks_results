"""Specs for the Milan relaunch (amended pre-registered rule, RELEASE_CHECKLIST.md 2026-11-14 ~14:00).

campaign/scs332m/campaign.json: every non-GPU shard of scs332, with "campaign": "scs332m".
Every November CPU row comes from these (run with --require-cpu 25/1, fresh directories).
campaign/scs332_relaunch/campaign.json: those plus the GPU shards of scs332 that no
orchestrator log reports finished (they resume under scs332).
Run after the scs332 orchestrator has stopped.
"""
import json
import re
from pathlib import Path

H = Path("/Users/bodonoghue/git/sb-refresh")
LOGS = Path("/Users/bodonoghue/scs33_tools/refresh_332/logs")
spec = json.loads((H / "campaign/scs332/campaign.json").read_text())
done = set()
for log in sorted(LOGS.glob("campaign_scs332_2026*.log")):
    for m in re.finditer(r"^(\S+)\s+rows=\s*\d+\s+[\d.]+ min\s+spent~\$\s*[\d.]+\s*$", log.read_text(), re.M):
        done.add(m.group(1))
cpu = [dict(s, campaign="scs332m") for s in spec if s["runner"] != "gpu"]
gpu_left = [s for s in spec if s["runner"] == "gpu" and s["name"] not in done]
gpu_done = [s for s in spec if s["runner"] == "gpu" and s["name"] in done]
(H / "campaign/scs332m").mkdir(exist_ok=True)
(H / "campaign/scs332m/campaign.json").write_text(json.dumps(cpu, indent=1))
(H / "campaign/scs332_relaunch").mkdir(exist_ok=True)
# GPU first: they are the long pole
(H / "campaign/scs332_relaunch/campaign.json").write_text(json.dumps(gpu_left + cpu, indent=1))
print(f"CPU shards (scs332m): {len(cpu)}, est {sum(s['est_hours'] for s in cpu):.1f} h")
print(f"GPU shards finished: {len(gpu_done)}; to run/resume: {len(gpu_left)}, est {sum(s['est_hours'] for s in gpu_left):.1f} h")
