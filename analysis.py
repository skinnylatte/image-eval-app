"""
Analysis functions for aggregating red team data across participants.
Generates summary statistics and identifies patterns for the paper.
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from typing import Dict, List

from config import SCORE_FIELDS


# ---------------------------------------------------------------------------
# Core aggregation (one function, parameterized)
# ---------------------------------------------------------------------------

def aggregate_scores(annotations: List[Dict], group_field: str) -> Dict:
    """
    Group annotations by `group_field` and compute mean/std for each score dimension.
    `group_field` is a key in the annotation dict (e.g. "model_name", "category", "background").
    """
    buckets = defaultdict(lambda: {f: [] for f in SCORE_FIELDS})

    for ann in annotations:
        if not ann.get("scores"):
            continue
        group = ann.get(group_field)
        if not group:
            continue
        for field in SCORE_FIELDS:
            val = ann["scores"].get(field)
            if val is not None:
                buckets[group][field].append(val)

    results = {}
    for group, scores in buckets.items():
        n = len(scores[SCORE_FIELDS[0]])
        entry = {"n": n}
        for field in SCORE_FIELDS:
            vals = scores[field]
            entry[f"{field}_mean"] = float(np.mean(vals)) if vals else None
            entry[f"{field}_std"] = float(np.std(vals)) if vals else None
        results[group] = entry

    return results


# ---------------------------------------------------------------------------
# Refusal analysis
# ---------------------------------------------------------------------------

def analyze_refusals(annotations: List[Dict]) -> Dict:
    by_model = defaultdict(list)
    by_category = defaultdict(list)

    for ann in annotations:
        if ann.get("status") != "refused":
            continue
        entry = {
            "prompt": ann["prompt"],
            "category": ann["category"],
            "note": ann.get("refusal_note", ""),
            "background": ann.get("background", ""),
        }
        by_model[ann["model_name"]].append(entry)
        by_category[ann["category"]].append({**entry, "model": ann["model_name"]})

    return {
        "by_model": dict(by_model),
        "by_category": dict(by_category),
        "total": sum(len(v) for v in by_model.values()),
    }


# ---------------------------------------------------------------------------
# Inter-rater reliability
# ---------------------------------------------------------------------------

def compute_inter_rater_reliability(annotations: List[Dict]) -> Dict:
    """
    Per-(prompt, model) agreement stats for shared prompts.
    For a full paper, compute Krippendorff's alpha (requires the `krippendorff` package).
    """
    shared = [a for a in annotations if a.get("prompt_type") == "shared" and a.get("scores")]

    groups = defaultdict(lambda: {f: [] for f in SCORE_FIELDS})
    raters = defaultdict(set)

    for ann in shared:
        key = (ann["prompt"], ann["model_name"])
        raters[key].add(ann["participant_id"])
        for field in SCORE_FIELDS:
            val = ann["scores"].get(field)
            if val is not None:
                groups[key][field].append(val)

    results = {}
    for (prompt, model), scores in groups.items():
        n = len(raters[(prompt, model)])
        entry = {"prompt": prompt, "model": model, "n_raters": n}
        for field in SCORE_FIELDS:
            vals = scores[field]
            if len(vals) >= 2:
                entry[f"{field}_mean"] = float(np.mean(vals))
                entry[f"{field}_std"] = float(np.std(vals))
                entry[f"{field}_range"] = int(max(vals) - min(vals))
            elif vals:
                entry[f"{field}_mean"] = float(vals[0])
                entry[f"{field}_std"] = 0.0
                entry[f"{field}_range"] = 0
        results[f"{prompt} | {model}"] = entry

    return results


# ---------------------------------------------------------------------------
# Key findings extraction
# ---------------------------------------------------------------------------

def extract_low_scores(annotations: List[Dict], threshold: int = 2) -> Dict[str, Dict[str, List]]:
    """Find annotations where any score dimension is at or below `threshold`."""
    findings = {f: defaultdict(list) for f in SCORE_FIELDS}

    note_fields = {
        "authenticity": "authenticity_note",
        "diversity": "expectation",
        "respectfulness": "harm_note",
    }

    for ann in annotations:
        if not ann.get("scores"):
            continue
        model = ann["model_name"]
        for field in SCORE_FIELDS:
            val = ann["scores"].get(field)
            if val is not None and val <= threshold:
                findings[field][model].append({
                    "prompt": ann["prompt"],
                    "note": ann.get(note_fields[field], ""),
                    "score": val,
                    "background": ann.get("background", ""),
                })

    return findings


def extract_quotes(annotations: List[Dict], min_length: int = 50) -> List[Dict]:
    """Collect substantive participant quotes from text fields."""
    quotes = []
    for ann in annotations:
        for field in ["harm_note", "authenticity_note", "expectation"]:
            note = ann.get(field, "")
            if note and len(note) >= min_length:
                quotes.append({
                    "participant": ann["participant_id"],
                    "background": ann.get("background", ""),
                    "model": ann["model_name"],
                    "prompt": ann["prompt"],
                    "field": field,
                    "quote": note,
                })
    return quotes


# ---------------------------------------------------------------------------
# Summary table (for paper)
# ---------------------------------------------------------------------------

def summary_table(annotations: List[Dict]) -> pd.DataFrame:
    rows = []
    for label, field in [("By Model", "model_name"), ("By Category", "category"), ("By Background", "background")]:
        for group, stats in aggregate_scores(annotations, field).items():
            row = {"Dimension": label, "Group": group, "n": stats["n"]}
            for sf in SCORE_FIELDS:
                m, s = stats.get(f"{sf}_mean"), stats.get(f"{sf}_std")
                row[f"{sf.title()} (M +/- SD)"] = f"{m:.2f} +/- {s:.2f}" if m is not None else "N/A"
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Full report
# ---------------------------------------------------------------------------

def generate_report(annotations: List[Dict]) -> str:
    participants = set(a["participant_id"] for a in annotations)
    backgrounds = set(a.get("background", "Unknown") for a in annotations)
    refused = [a for a in annotations if a.get("status") == "refused"]
    shared = [a for a in annotations if a.get("prompt_type") == "shared"]
    free = [a for a in annotations if a.get("prompt_type") == "free"]

    lines = [
        "# Red Team Evaluation: Summary Findings\n",
        f"**Total Annotations:** {len(annotations)}  ",
        f"**Participants:** {len(participants)}  ",
        f"**Communities:** {', '.join(sorted(backgrounds))}  ",
        f"**Shared / Free:** {len(shared)} / {len(free)}  ",
        f"**Model Refusals:** {len(refused)}\n",
        "## Summary Statistics\n",
        summary_table(annotations).to_markdown(index=False),
        "\n",
    ]

    # Inter-rater reliability
    irr = compute_inter_rater_reliability(annotations)
    if irr:
        lines.append("## Inter-Rater Reliability (Shared Prompts)\n")
        for key, stats in irr.items():
            lines.append(f"**{key}** (n={stats['n_raters']} raters)  ")
            for f in SCORE_FIELDS:
                m = stats.get(f"{f}_mean")
                if isinstance(m, float):
                    lines.append(f"  - {f.title()}: M={m:.2f}, SD={stats[f'{f}_std']:.2f}, Range={stats[f'{f}_range']}")
            lines.append("")

    # Refusals
    ref = analyze_refusals(annotations)
    if ref["total"]:
        lines.append("## Model Refusals\n")
        for model, entries in ref["by_model"].items():
            lines.append(f"**{model}:** {len(entries)} refusals  ")
            for e in entries[:3]:
                lines.append(f'  - "{e["prompt"]}" — {e["note"][:100]}')
            lines.append("")

    # Low scores
    findings = extract_low_scores(annotations)
    for field in SCORE_FIELDS:
        items = findings[field]
        if not items:
            continue
        lines.append(f"## Low {field.title()} (score <= 2)\n")
        for model, issues in items.items():
            lines.append(f"**{model}:** {len(issues)} annotations  ")
            for iss in issues[:3]:
                bg = f" [{iss['background']}]" if iss.get("background") else ""
                note = (iss["note"][:120] or "(no note)")
                lines.append(f'  - "{iss["prompt"]}"{bg}: {note}')
            lines.append("")

    # Quotes
    quotes = extract_quotes(annotations)[:10]
    if quotes:
        lines.append("## Selected Participant Insights\n")
        for i, q in enumerate(quotes, 1):
            bg = f" [{q['background']}]" if q.get("background") else ""
            lines.append(f'### {i}. {q["model"]} — "{q["prompt"]}"{bg}\n')
            lines.append(f"> {q['quote']}\n")

    return "\n".join(lines)
