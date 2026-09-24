"""M1 isolated provider boundary. Missing access never produces a fabricated model result."""

ALLOWED_TOOLS = frozenset(
    {
        "market.get_snapshot",
        "portfolio.get_exposure",
        "planning.run_scenario",
        "orders.preview_intent",
    }
)


def authorize_tool(tool, privacy_mode="LOCAL_ONLY"):
    if tool not in ALLOWED_TOOLS:
        raise PermissionError("TOOL_DENIED")
    if privacy_mode == "LOCAL_ONLY":
        raise PermissionError("CLOUD_DISABLED")


def assess_public_text(text, provider="jev"):
    return {
        "provider": provider,
        "disposition": "ABSTAIN",
        "verification": "NOT_RUN_MISSING_CREDENTIALS",
        "reason": "Externe modeluitvoering is niet aangesloten; LOCAL_ONLY blijft actief.",
        "answers": [],
    }
