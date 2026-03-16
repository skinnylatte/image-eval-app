"""
Analysis script for aggregating red team data across all participants
Generates summary statistics and identifies patterns for paper

Updated to handle:
- Anonymized participant IDs
- Participant background/community field
- Shared vs free prompts
- Model refusals
- Renamed "respectfulness" metric (was "harm")
- Inter-rater reliability for shared prompts
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List
from collections import defaultdict

DATA_DIR = "red_team_data"
SCORE_FIELDS = ["authenticity", "diversity", "respectfulness"]


def load_all_annotations() -> List[Dict]:
    """Load all participant annotations"""
    annotations = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith("_annotations.json") and not filename.startswith("_"):
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                participant_annotations = json.load(f)
                annotations.extend(participant_annotations)
    return annotations


def load_identity_map() -> Dict:
    """Load the identity mapping (for facilitator use only)"""
    path = os.path.join(DATA_DIR, "_identity_map.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def analyze_by_model(annotations: List[Dict]) -> Dict:
    """Analyze scores aggregated by model"""
    model_stats = defaultdict(lambda: {f: [] for f in SCORE_FIELDS})

    for ann in annotations:
        if not ann.get("scores"):
            continue
        model = ann["model_name"]
        for field in SCORE_FIELDS:
            if ann["scores"].get(field) is not None:
                model_stats[model][field].append(ann["scores"][field])

    results = {}
    for model, scores in model_stats.items():
        results[model] = {"n_annotations": len(scores[SCORE_FIELDS[0]])}
        for field in SCORE_FIELDS:
            if scores[field]:
                results[model][f"{field}_mean"] = np.mean(scores[field])
                results[model][f"{field}_std"] = np.std(scores[field])
            else:
                results[model][f"{field}_mean"] = None
                results[model][f"{field}_std"] = None
    return results


def analyze_by_category(annotations: List[Dict]) -> Dict:
    """Analyze bias patterns by category"""
    category_stats = defaultdict(lambda: {f: [] for f in SCORE_FIELDS})

    for ann in annotations:
        if not ann.get("scores"):
            continue
        cat = ann["category"]
        for field in SCORE_FIELDS:
            if ann["scores"].get(field) is not None:
                category_stats[cat][field].append(ann["scores"][field])

    results = {}
    for cat, scores in category_stats.items():
        results[cat] = {"n_annotations": len(scores[SCORE_FIELDS[0]])}
        for field in SCORE_FIELDS:
            if scores[field]:
                results[cat][f"{field}_mean"] = np.mean(scores[field])
                results[cat][f"{field}_std"] = np.std(scores[field])
            else:
                results[cat][f"{field}_mean"] = None
                results[cat][f"{field}_std"] = None
    return results


def analyze_by_background(annotations: List[Dict]) -> Dict:
    """Analyze scores by participant background/community"""
    bg_stats = defaultdict(lambda: {f: [] for f in SCORE_FIELDS})

    for ann in annotations:
        if not ann.get("scores") or not ann.get("background"):
            continue
        bg = ann["background"]
        for field in SCORE_FIELDS:
            if ann["scores"].get(field) is not None:
                bg_stats[bg][field].append(ann["scores"][field])

    results = {}
    for bg, scores in bg_stats.items():
        results[bg] = {"n_annotations": len(scores[SCORE_FIELDS[0]])}
        for field in SCORE_FIELDS:
            if scores[field]:
                results[bg][f"{field}_mean"] = np.mean(scores[field])
                results[bg][f"{field}_std"] = np.std(scores[field])
            else:
                results[bg][f"{field}_mean"] = None
                results[bg][f"{field}_std"] = None
    return results


def analyze_refusals(annotations: List[Dict]) -> Dict:
    """Analyze model refusal patterns"""
    refusals_by_model = defaultdict(list)
    refusals_by_category = defaultdict(list)

    for ann in annotations:
        if ann.get("status") != "refused":
            continue
        refusals_by_model[ann["model_name"]].append({
            "prompt": ann["prompt"],
            "category": ann["category"],
            "note": ann.get("refusal_note", ""),
            "background": ann.get("background", ""),
        })
        refusals_by_category[ann["category"]].append({
            "prompt": ann["prompt"],
            "model": ann["model_name"],
            "note": ann.get("refusal_note", ""),
        })

    return {
        "by_model": dict(refusals_by_model),
        "by_category": dict(refusals_by_category),
        "total": sum(len(v) for v in refusals_by_model.values()),
    }


def compute_inter_rater_reliability(annotations: List[Dict]) -> Dict:
    """
    Compute inter-rater agreement for shared prompts.
    Returns per-prompt, per-model agreement statistics.
    For a full paper, use Krippendorff's alpha (requires krippendorff package).
    """
    shared = [a for a in annotations if a.get("prompt_type") == "shared" and a.get("scores")]

    # Group by (prompt, model)
    groups = defaultdict(lambda: {f: [] for f in SCORE_FIELDS})
    rater_counts = defaultdict(set)

    for ann in shared:
        key = (ann["prompt"], ann["model_name"])
        rater_counts[key].add(ann["participant_id"])
        for field in SCORE_FIELDS:
            if ann["scores"].get(field) is not None:
                groups[key][field].append(ann["scores"][field])

    results = {}
    for key, scores in groups.items():
        prompt, model = key
        n_raters = len(rater_counts[key])
        entry = {"prompt": prompt, "model": model, "n_raters": n_raters}

        for field in SCORE_FIELDS:
            vals = scores[field]
            if len(vals) >= 2:
                entry[f"{field}_mean"] = np.mean(vals)
                entry[f"{field}_std"] = np.std(vals)
                entry[f"{field}_range"] = max(vals) - min(vals)
            elif vals:
                entry[f"{field}_mean"] = vals[0]
                entry[f"{field}_std"] = 0
                entry[f"{field}_range"] = 0

        results[f"{prompt} | {model}"] = entry

    return results


def extract_key_findings(annotations: List[Dict]) -> Dict:
    """Extract key qualitative insights from participant feedback"""
    findings = {
        "low_authenticity": defaultdict(list),
        "low_diversity": defaultdict(list),
        "low_respectfulness": defaultdict(list),
        "refusals": defaultdict(list),
        "participant_quotes": [],
    }

    for ann in annotations:
        model = ann["model_name"]

        if ann.get("status") == "refused":
            findings["refusals"][model].append({
                "prompt": ann["prompt"],
                "note": ann.get("refusal_note", ""),
                "background": ann.get("background", ""),
            })
            continue

        if not ann.get("scores"):
            continue

        if ann["scores"].get("authenticity") is not None and ann["scores"]["authenticity"] <= 2:
            findings["low_authenticity"][model].append({
                "prompt": ann["prompt"],
                "note": ann.get("authenticity_note", ""),
                "score": ann["scores"]["authenticity"],
                "background": ann.get("background", ""),
            })

        if ann["scores"].get("diversity") is not None and ann["scores"]["diversity"] <= 2:
            findings["low_diversity"][model].append({
                "prompt": ann["prompt"],
                "note": ann.get("expectation", ""),
                "score": ann["scores"]["diversity"],
                "background": ann.get("background", ""),
            })

        if ann["scores"].get("respectfulness") is not None and ann["scores"]["respectfulness"] <= 2:
            findings["low_respectfulness"][model].append({
                "prompt": ann["prompt"],
                "note": ann.get("harm_note", ""),
                "score": ann["scores"]["respectfulness"],
                "background": ann.get("background", ""),
            })

        # Collect substantive quotes
        for field in ["harm_note", "authenticity_note", "expectation"]:
            note = ann.get(field, "")
            if note and len(note) > 50:
                findings["participant_quotes"].append({
                    "participant": ann["participant_id"],
                    "background": ann.get("background", ""),
                    "model": model,
                    "prompt": ann["prompt"],
                    "field": field,
                    "quote": note,
                })

    return findings


def generate_summary_table(annotations: List[Dict]) -> pd.DataFrame:
    """Generate summary table for paper"""
    data = []

    for label, analysis_fn in [
        ("By Model", analyze_by_model),
        ("By Category", analyze_by_category),
        ("By Background", analyze_by_background),
    ]:
        analysis = analysis_fn(annotations)
        for key, stats in analysis.items():
            row = {"Dimension": label, "Group": key, "n": stats["n_annotations"]}
            for field in SCORE_FIELDS:
                mean = stats.get(f"{field}_mean")
                std = stats.get(f"{field}_std")
                if mean is not None:
                    row[f"{field.title()} (M +/- SD)"] = f"{mean:.2f} +/- {std:.2f}"
                else:
                    row[f"{field.title()} (M +/- SD)"] = "N/A"
            data.append(row)

    return pd.DataFrame(data)


def generate_report(annotations: List[Dict]) -> str:
    """Generate markdown report of findings"""
    report = []

    total = len(annotations)
    scored = [a for a in annotations if a.get("scores")]
    refused = [a for a in annotations if a.get("status") == "refused"]
    shared = [a for a in annotations if a.get("prompt_type") == "shared"]
    free = [a for a in annotations if a.get("prompt_type") == "free"]
    participants = set(a["participant_id"] for a in annotations)
    backgrounds = set(a.get("background", "Unknown") for a in annotations)

    report.append("# Red Team Evaluation: Summary Findings\n\n")
    report.append(f"**Total Annotations:** {total}\n")
    report.append(f"**Participants:** {len(participants)}\n")
    report.append(f"**Communities Represented:** {', '.join(backgrounds)}\n")
    report.append(f"**Shared Prompt Annotations:** {len(shared)}\n")
    report.append(f"**Free Exploration Annotations:** {len(free)}\n")
    report.append(f"**Model Refusals:** {len(refused)}\n\n")

    # Summary table
    report.append("## Summary Statistics\n\n")
    summary_df = generate_summary_table(annotations)
    report.append(summary_df.to_markdown(index=False))
    report.append("\n\n")

    # Inter-rater reliability
    irr = compute_inter_rater_reliability(annotations)
    if irr:
        report.append("## Inter-Rater Reliability (Shared Prompts)\n\n")
        for key, stats in irr.items():
            report.append(f"**{key}** (n={stats['n_raters']} raters)\n")
            for field in SCORE_FIELDS:
                mean = stats.get(f"{field}_mean", "?")
                std = stats.get(f"{field}_std", "?")
                rng = stats.get(f"{field}_range", "?")
                if isinstance(mean, float):
                    report.append(f"  - {field.title()}: M={mean:.2f}, SD={std:.2f}, Range={rng}\n")
            report.append("\n")

    # Refusal analysis
    refusal_analysis = analyze_refusals(annotations)
    if refusal_analysis["total"] > 0:
        report.append("## Model Refusals\n\n")
        for model, refs in refusal_analysis["by_model"].items():
            report.append(f"**{model}:** {len(refs)} refusals\n")
            for ref in refs[:3]:
                report.append(f"  - \"{ref['prompt']}\" — {ref['note'][:100]}\n")
            report.append("\n")

    # Key findings
    findings = extract_key_findings(annotations)

    for category, label in [
        ("low_authenticity", "Low Authenticity (score <= 2)"),
        ("low_diversity", "Low Diversity (score <= 2)"),
        ("low_respectfulness", "Low Respectfulness (score <= 2)"),
    ]:
        items = findings[category]
        if items:
            report.append(f"## {label}\n\n")
            for model, issues in items.items():
                report.append(f"**{model}:** {len(issues)} annotations\n")
                for issue in issues[:3]:
                    bg = f" [{issue['background']}]" if issue.get("background") else ""
                    note = issue["note"][:120] if issue["note"] else "(no note)"
                    report.append(f"  - \"{issue['prompt']}\"{bg}: {note}\n")
                report.append("\n")

    # Selected quotes
    quotes = findings["participant_quotes"][:10]
    if quotes:
        report.append("## Selected Participant Insights\n\n")
        for i, q in enumerate(quotes):
            bg = f" [{q['background']}]" if q.get("background") else ""
            report.append(f"### {i + 1}. {q['model']} — \"{q['prompt']}\"{bg}\n\n")
            report.append(f"> {q['quote']}\n\n")

    return "".join(report)


def main():
    """Run analysis pipeline"""
    print("Loading annotations...")
    annotations = load_all_annotations()
    print(f"  Loaded {len(annotations)} annotations")

    if not annotations:
        print("No annotations found. Run the Streamlit app first.")
        return

    participants = set(a["participant_id"] for a in annotations)
    backgrounds = set(a.get("background", "Unknown") for a in annotations)
    print(f"  Participants: {len(participants)}")
    print(f"  Communities: {', '.join(backgrounds)}")

    print("\nBy model:")
    model_stats = analyze_by_model(annotations)
    for model, stats in model_stats.items():
        print(f"\n  {model} (n={stats['n_annotations']}):")
        for field in SCORE_FIELDS:
            mean = stats.get(f"{field}_mean")
            std = stats.get(f"{field}_std")
            if mean is not None:
                print(f"    {field.title()}: {mean:.2f} +/- {std:.2f}")

    print("\nBy background:")
    bg_stats = analyze_by_background(annotations)
    for bg, stats in bg_stats.items():
        print(f"\n  {bg} (n={stats['n_annotations']}):")
        for field in SCORE_FIELDS:
            mean = stats.get(f"{field}_mean")
            std = stats.get(f"{field}_std")
            if mean is not None:
                print(f"    {field.title()}: {mean:.2f} +/- {std:.2f}")

    refusal_analysis = analyze_refusals(annotations)
    if refusal_analysis["total"] > 0:
        print(f"\nRefusals: {refusal_analysis['total']} total")
        for model, refs in refusal_analysis["by_model"].items():
            print(f"  {model}: {len(refs)}")

    irr = compute_inter_rater_reliability(annotations)
    if irr:
        print("\nInter-rater reliability (shared prompts):")
        for key, stats in irr.items():
            print(f"  {key} (n={stats['n_raters']} raters):")
            for field in SCORE_FIELDS:
                mean = stats.get(f"{field}_mean")
                rng = stats.get(f"{field}_range")
                if mean is not None:
                    print(f"    {field.title()}: M={mean:.2f}, Range={rng}")

    print("\nGenerating report...")
    report = generate_report(annotations)
    with open("red_team_findings.md", 'w') as f:
        f.write(report)
    print("  Saved to red_team_findings.md")

    summary_df = generate_summary_table(annotations)
    summary_df.to_csv("red_team_summary.csv", index=False)
    print("  Saved to red_team_summary.csv")

    print("\nSummary table:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        print(f"Error: {DATA_DIR} directory not found")
        print("Run the Streamlit app first to generate data")
    else:
        main()
