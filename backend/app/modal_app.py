"""Modal Serverless Group Intelligence Engine for TastePilot AI.
Reuses existing negotiation math and provides candidate-level fairness and counterfactuals.
"""
from typing import Any
import modal

app = modal.App("tastepilot-group-intelligence")

image = modal.Image.debian_slim(python_version="3.12").pip_install("pydantic>=2.0.0", "fastapi[standard]")


def compute_candidate_fairness(candidates: list[dict], labels: list[str]) -> list[dict]:
    """Calculate candidate-level fairness metrics across all group members."""
    rankings = []
    for c in candidates:
        ev_map = {e["label"]: e.get("proxy", 0.0) for e in c.get("member_evidence", [])}
        scores = {label: round(ev_map.get(label, 0.0), 4) for label in labels}
        values = list(scores.values()) or [0.0]
        min_satisfaction = min(values)
        avg_satisfaction = round(sum(values) / max(1, len(values)), 4)
        rankings.append({
            "id": c["id"],
            "name": c["name"],
            "category": c.get("category", "place"),
            "member_scores": scores,
            "min_satisfaction": round(min_satisfaction, 4),
            "avg_satisfaction": avg_satisfaction,
            "cost": c.get("cost"),
        })
    # Sort candidates by max-min satisfaction, then average satisfaction
    rankings.sort(key=lambda r: (-r["min_satisfaction"], -r["avg_satisfaction"], r["id"]))
    return rankings


def run_counterfactuals(candidates: list[dict], all_profiles: list[dict], max_stops: int, effective_budget: float, provisional: bool, selected_ids: list[str]) -> list[dict]:
    """Calculate leave-one-member-out counterfactuals: how choices change if one member is removed."""
    from itertools import combinations
    counterfactuals = []
    base_selected = set(selected_ids)
    all_labels = [p["label"] for p in all_profiles]

    if len(all_profiles) <= 1:
        return []

    pool = sorted(candidates, key=lambda c: c["id"])[:20]
    if not provisional:
        pool = [c for c in pool if c.get("cost") is not None]

    if not pool:
        return []

    id_to_name = {c["id"]: c["name"] for c in pool}

    for excluded in all_profiles:
        sub_profiles = [p for p in all_profiles if p["label"] != excluded["label"]]
        sub_labels = [p["label"] for p in sub_profiles]
        best_cf, best_cf_key = [], None

        for size in range(1, min(max_stops, len(pool)) + 1):
            for subset in combinations(pool, size):
                known_cost = sum(c.get("cost") or 0 for c in subset)
                if known_cost > effective_budget:
                    continue
                # coverage for sub-group
                values = {
                    label: max((e.get("proxy", 0.0) for c in subset for e in c.get("member_evidence", []) if e.get("label") == label), default=0.0)
                    for label in sub_labels
                }
                floor = min(values.values()) if values else 0.0
                mean = (sum(values.values()) / len(sub_labels)) if sub_labels else 0.0
                key = (floor, mean, len({c.get("category") for c in subset}), len(subset), -known_cost)
                if best_cf_key is None or key > best_cf_key:
                    best_cf, best_cf_key = list(subset), key

        cf_ids = [c["id"] for c in best_cf]
        cf_set = set(cf_ids)
        changed = cf_set != base_selected
        cf_names = [id_to_name.get(cid, cid) for cid in cf_ids]
        base_names = [id_to_name.get(cid, cid) for cid in selected_ids]

        if changed:
            added = [n for n in cf_names if n not in base_names]
            removed = [n for n in base_names if n not in cf_names]
            explanation = (
                f"Without {excluded['label']}, the group would have chosen "
                f"{', '.join(added) or 'a different subset'} instead of {', '.join(removed) or 'the compromise'}."
            )
        else:
            explanation = (
                f"Even without {excluded['label']}, the group compromise remains identical. "
                "This choice aligns well with the rest of the party."
            )

        counterfactuals.append({
            "excluded_member": excluded["label"],
            "changed": changed,
            "would_select_ids": cf_ids,
            "would_select_names": cf_names,
            "explanation": explanation,
        })
    return counterfactuals


def solve_group_optimization(payload: dict[str, Any]) -> dict[str, Any]:
    """Core deterministic optimization engine running inside Modal."""
    from itertools import combinations
    import time

    start = time.perf_counter()
    candidates = payload["candidates"]
    intent = payload["intent"]
    member_profiles = payload["member_profiles"]
    provisional = payload.get("provisional", False)
    max_stops = intent.get("max_stops", 3)
    budget = payload.get("effective_budget", intent.get("budget", 150))

    labels = [p["label"] for p in member_profiles]
    pool = sorted(candidates, key=lambda c: c["id"])[:20]
    if not provisional:
        pool = [c for c in pool if c.get("cost") is not None]

    def run_opt(objective: str = "fair", ablate: bool = False):
        best, best_key, best_coverage = [], None, dict.fromkeys(labels, 0.0)
        examined = 0
        for size in range(1, min(max_stops, len(pool)) + 1):
            for subset in combinations(pool, size):
                examined += 1
                known_cost = sum(c.get("cost") or 0 for c in subset)
                if known_cost > budget:
                    continue
                values = {
                    label: max((e.get("explicit_alignment" if ablate else "proxy", 0.0)
                                for c in subset for e in c.get("member_evidence", [])
                                if e.get("label") == label), default=0.0)
                    for label in labels
                }
                floor = min(values.values()) if values else 0.0
                mean = (sum(values.values()) / len(labels)) if values else 0.0
                primary = (floor, mean) if objective == "fair" else (mean, floor)
                key = (*primary, len({c.get("category") for c in subset}), len(subset), -known_cost)
                if best_key is None or key > best_key:
                    best, best_key, best_coverage = list(subset), key, values
        return best, {
            "member_coverage": {k: round(v, 4) for k, v in best_coverage.items()},
            "minimum_coverage": round(min(best_coverage.values()), 4) if best_coverage else 0.0,
            "mean_coverage": round(sum(best_coverage.values()) / max(1, len(labels)), 4) if best_coverage else 0.0,
            "subsets_examined": examined,
            "known_cost": round(sum(c.get("cost") or 0 for c in best), 2),
            "unknown_cost_count": sum(c.get("cost") is None for c in best),
            "ids": [c["id"] for c in best]
        }

    fair_best, fair_rep = run_opt(objective="fair", ablate=False)
    mean_best, mean_rep = run_opt(objective="mean", ablate=False)
    ablate_best, ablate_rep = run_opt(objective="fair", ablate=True)

    selected_ids = [c["id"] for c in fair_best]
    candidate_rankings = compute_candidate_fairness(candidates, labels)
    counterfactuals = run_counterfactuals(candidates, member_profiles, max_stops, budget, provisional, selected_ids)

    latency_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "engine": "modal",
        "strategy": "Maximize minimum best-stop ordinal coverage; then mean coverage, diversity and cardinality.",
        "is_provisional": provisional,
        "selected_ids": selected_ids,
        "fair": fair_rep,
        "mean_objective": mean_rep,
        "without_taste": ablate_rep,
        "minimum_coverage_delta": round(fair_rep["minimum_coverage"] - mean_rep["minimum_coverage"], 4),
        "mean_coverage_tradeoff": round(fair_rep["mean_coverage"] - mean_rep["mean_coverage"], 4),
        "candidate_rankings": candidate_rankings,
        "counterfactuals": counterfactuals,
        "metrics": {
            "execution_ms": latency_ms,
            "pool_size": len(pool),
            "subsets_examined": fair_rep["subsets_examined"],
            "profiles_modeled": len(member_profiles),
        }
    }


@app.function(image=image, timeout=30)
def optimize(payload: dict[str, Any]) -> dict[str, Any]:
    """Modal function for group optimization."""
    return solve_group_optimization(payload)


@app.function(image=image, timeout=30)
@modal.fastapi_endpoint(method="POST")
def web_optimize(payload: dict[str, Any]) -> dict[str, Any]:
    """Modal HTTP web endpoint callable directly from FastAPI backend."""
    return solve_group_optimization(payload)
