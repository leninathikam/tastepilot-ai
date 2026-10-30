"""Client interface for Modal serverless group intelligence with resilient local fallback."""
import logging
import os
import time
from typing import Any
import httpx
from .modal_app import solve_group_optimization

logger = logging.getLogger("tastepilot.modal")


def solve_group_locally(payload: dict[str, Any], fallback_reason: str = "") -> dict[str, Any]:
    """Execute fairness optimization and counterfactuals locally within the FastAPI process."""
    result = solve_group_optimization(payload)
    result["engine"] = "local_fallback"
    if fallback_reason:
        result["fallback_reason"] = fallback_reason
    return result


async def optimize_group_intelligence(
    candidates: list[Any],
    intent: Any,
    member_profiles: list[dict],
    provisional: bool = False,
    timeout_sec: float = 6.0,
) -> dict[str, Any]:
    """Call Modal serverless endpoint with automatic failover to local execution."""
    payload = {
        "candidates": [c.model_dump(mode="json") if hasattr(c, "model_dump") else c for c in candidates],
        "intent": intent.model_dump(mode="json") if hasattr(intent, "model_dump") else intent,
        "member_profiles": member_profiles,
        "effective_budget": getattr(intent, "effective_budget", getattr(intent, "budget", 150)),
        "provisional": provisional,
    }

    modal_url = os.getenv("MODAL_API_URL", "").strip()
    modal_enabled = os.getenv("MODAL_ENABLED", "true").strip().casefold() not in ("false", "0", "no")
    modal_auth = os.getenv("MODAL_AUTH_TOKEN", "").strip()

    if not modal_enabled or not modal_url:
        reason = "Modal disabled by configuration" if not modal_enabled else "MODAL_API_URL not configured"
        return solve_group_locally(payload, fallback_reason=reason)

    headers = {"Content-Type": "application/json"}
    if modal_auth:
        headers["Authorization"] = f"Bearer {modal_auth}"

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.post(modal_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            data["engine"] = "modal"
            data["metrics"]["roundtrip_ms"] = round((time.perf_counter() - start) * 1000, 2)
            return data
    except httpx.TimeoutException:
        logger.warning("Modal call timed out after %.1fs; failing over to local engine", timeout_sec)
        return solve_group_locally(payload, fallback_reason=f"Modal timed out after {timeout_sec}s")
    except Exception as exc:
        logger.warning("Modal call failed (%s); failing over to local engine", exc)
        return solve_group_locally(payload, fallback_reason=f"Modal error: {type(exc).__name__}")
