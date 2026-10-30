"""Automated test suite for Modal-powered group intelligence, fairness calculations,
counterfactual explanations, and resilient local fallback.
"""
import asyncio
import pytest
import httpx
from datetime import date
from backend.app.models import Candidate, Intent, Companion, Seed, MemberEvidence
from backend.app.modal_app import solve_group_optimization, compute_candidate_fairness, run_counterfactuals
from backend.app.modal_client import optimize_group_intelligence, solve_group_locally


def make_mock_candidate(cid: str, name: str, cost: float | None = 25.0, proxies: dict[str, float] | None = None) -> Candidate:
    proxies = proxies or {"You": 0.5, "Alex": 0.5}
    ev = [
        MemberEvidence(
            label=lbl,
            source="qloo",
            resolved_ids=["id1"],
            returned_rank=1,
            ordinal_signal=val,
            explicit_alignment=val,
            matched_interests=["music"],
            proxy=val,
            raw_query={},
            note="test"
        )
        for lbl, val in proxies.items()
    ]
    return Candidate(
        id=cid,
        name=name,
        category="place",
        tags=["music", "food"],
        source="qloo",
        cost=cost,
        taste_rank=1,
        taste_score=0.8,
        member_evidence=ev
    )


def test_candidate_level_fairness_calculation():
    c1 = make_mock_candidate("c1", "Place 1", proxies={"You": 0.9, "Alex": 0.3})
    c2 = make_mock_candidate("c2", "Place 2", proxies={"You": 0.6, "Alex": 0.6})
    labels = ["You", "Alex"]
    
    candidates_dict = [c.model_dump(mode="json") for c in [c1, c2]]
    rankings = compute_candidate_fairness(candidates_dict, labels)
    
    assert len(rankings) == 2
    # Place 2 has min_satisfaction 0.6; Place 1 has min_satisfaction 0.3.
    # Max-min should rank Place 2 first!
    assert rankings[0]["id"] == "c2"
    assert rankings[0]["min_satisfaction"] == 0.6
    assert rankings[0]["avg_satisfaction"] == 0.6
    assert rankings[1]["id"] == "c1"
    assert rankings[1]["min_satisfaction"] == 0.3
    assert rankings[1]["avg_satisfaction"] == 0.6


def test_leave_one_member_out_counterfactuals():
    # Candidate A satisfies You (0.9), Alex (0.1)
    # Candidate B satisfies You (0.1), Alex (0.9)
    # Candidate C satisfies You (0.6), Alex (0.6) - the balanced compromise
    cA = make_mock_candidate("cA", "You's Favorite", proxies={"You": 0.9, "Alex": 0.1})
    cB = make_mock_candidate("cB", "Alex's Favorite", proxies={"You": 0.1, "Alex": 0.9})
    cC = make_mock_candidate("cC", "Compromise Spot", proxies={"You": 0.6, "Alex": 0.6})
    
    candidates = [cA, cB, cC]
    c_dicts = [c.model_dump(mode="json") for c in candidates]
    profiles = [
        {"label": "You", "seeds": [{"name": "A", "category": "artist"}], "interests": []},
        {"label": "Alex", "seeds": [{"name": "B", "category": "artist"}], "interests": []},
    ]
    
    # Base group selection with max_stops=1: should pick cC (0.6 min) over cA or cB (0.1 min)
    payload = {
        "candidates": c_dicts,
        "intent": {"max_stops": 1, "budget": 100},
        "member_profiles": profiles,
        "effective_budget": 100,
        "provisional": False,
    }
    result = solve_group_optimization(payload)
    assert result["selected_ids"] == ["cC"]
    
    cfs = result["counterfactuals"]
    assert len(cfs) == 2
    
    # If Alex is excluded, the group should choose cA (0.9 satisfaction for You)
    alex_cf = next(cf for cf in cfs if cf["excluded_member"] == "Alex")
    assert alex_cf["changed"] is True
    assert alex_cf["would_select_ids"] == ["cA"]
    assert "Without Alex" in alex_cf["explanation"]
    
    # If You is excluded, the group should choose cB (0.9 satisfaction for Alex)
    you_cf = next(cf for cf in cfs if cf["excluded_member"] == "You")
    assert you_cf["changed"] is True
    assert you_cf["would_select_ids"] == ["cB"]
    assert "Without You" in you_cf["explanation"]


def test_conflicting_preferences_fairness_optimization():
    # 3 members with diverging tastes
    c1 = make_mock_candidate("c1", "Indie Rock Venue", proxies={"You": 0.9, "Alex": 0.2, "Jordan": 0.1})
    c2 = make_mock_candidate("c2", "Cinema & Cafe", proxies={"You": 0.2, "Alex": 0.8, "Jordan": 0.2})
    c3 = make_mock_candidate("c3", "Art Museum Cafe", proxies={"You": 0.5, "Alex": 0.5, "Jordan": 0.5})
    
    c_dicts = [c.model_dump(mode="json") for c in [c1, c2, c3]]
    profiles = [{"label": "You"}, {"label": "Alex"}, {"label": "Jordan"}]
    payload = {
        "candidates": c_dicts,
        "intent": {"max_stops": 1, "budget": 100},
        "member_profiles": profiles,
        "effective_budget": 100,
        "provisional": False,
    }
    result = solve_group_optimization(payload)
    # c3 has lowest individual floor of 0.5, beating c1 (0.1) and c2 (0.2)
    assert result["selected_ids"] == ["c3"]
    assert result["fair"]["minimum_coverage"] == 0.5


def test_empty_candidates_handling():
    payload = {
        "candidates": [],
        "intent": {"max_stops": 2, "budget": 100},
        "member_profiles": [{"label": "You"}, {"label": "Alex"}],
        "effective_budget": 100,
        "provisional": False,
    }
    result = solve_group_optimization(payload)
    assert result["selected_ids"] == []
    assert result["fair"]["minimum_coverage"] == 0.0
    assert result["candidate_rankings"] == []
    assert result["counterfactuals"] == []


def test_modal_client_fallback_when_disabled(monkeypatch):
    c = make_mock_candidate("c1", "Place 1")
    intent = Intent(date=date(2026, 10, 31), destination="Chicago", party_size=2, budget=100, companions=[Companion(label="Alex", seeds=[Seed(name="Khruangbin")])])
    
    # Explicitly disable Modal via environment variable to test local fallback
    monkeypatch.setenv("MODAL_ENABLED", "false")
    
    res = asyncio.run(optimize_group_intelligence(
        candidates=[c],
        intent=intent,
        member_profiles=[{"label": "You"}, {"label": "Alex"}],
        provisional=False
    ))
    assert res["engine"] == "local_fallback"
    assert "fallback_reason" in res
    assert res["selected_ids"] == ["c1"]


def test_modal_client_timeout_fallback(monkeypatch):
    c = make_mock_candidate("c1", "Place 1")
    intent = Intent(date=date(2026, 10, 31), destination="Chicago", party_size=2, budget=100, companions=[Companion(label="Alex", seeds=[Seed(name="Khruangbin")])])
    
    monkeypatch.setenv("MODAL_API_URL", "https://fake-modal-endpoint.run")
    
    # Mock httpx to raise TimeoutException
    async def timeout_post(*args, **kwargs):
        raise httpx.TimeoutException("Connection timed out")
    
    monkeypatch.setattr(httpx.AsyncClient, "post", timeout_post)
    
    res = asyncio.run(optimize_group_intelligence(
        candidates=[c],
        intent=intent,
        member_profiles=[{"label": "You"}, {"label": "Alex"}],
        provisional=False,
        timeout_sec=0.1
    ))
    assert res["engine"] == "local_fallback"
    assert "timed out" in res["fallback_reason"].lower()
    assert res["selected_ids"] == ["c1"]


def test_modal_client_server_error_fallback(monkeypatch):
    c = make_mock_candidate("c1", "Place 1")
    intent = Intent(date=date(2026, 10, 31), destination="Chicago", party_size=2, budget=100, companions=[Companion(label="Alex", seeds=[Seed(name="Khruangbin")])])
    
    monkeypatch.setenv("MODAL_API_URL", "https://fake-modal-endpoint.run")
    
    # Mock httpx to raise HTTPStatusError (500)
    async def error_post(*args, **kwargs):
        req = httpx.Request("POST", "https://fake-modal-endpoint.run")
        resp = httpx.Response(500, request=req)
        raise httpx.HTTPStatusError("Server Error", request=req, response=resp)
    
    monkeypatch.setattr(httpx.AsyncClient, "post", error_post)
    
    res = asyncio.run(optimize_group_intelligence(
        candidates=[c],
        intent=intent,
        member_profiles=[{"label": "You"}, {"label": "Alex"}],
        provisional=False
    ))
    assert res["engine"] == "local_fallback"
    assert "HTTPStatusError" in res["fallback_reason"]
    assert res["selected_ids"] == ["c1"]
