"""pytest: the validator as a pure function, and the whole server through an in-process client."""
import json
import pytest
from mcp.client import Client
import momentum_planner as mp

REQUEST = {"requestId": "r1", "kind": "routine",
           "commitments": [{"label": "Work", "days": ["mon", "tue", "wed", "thu", "fri"], "start": "09:00", "end": "17:00"}]}

def plan(**blocks_override):
    return {"format": "daily-momentum-ai-plan", "contractVersion": 1, "requestId": "r1", "kind": "routine",
            "name": "Calm weekday", "tagline": "Walk, work, sleep.", "description": "A plain weekday.",
            "routine": {"blocks": blocks_override.get("blocks", [
                {"start": "07:00", "durationMin": 30, "activity": "Walk", "category": "body", "essential": True},
                {"start": "09:00", "durationMin": 480, "activity": "Work", "category": "work", "essential": True},
                {"start": "22:00", "durationMin": 480, "activity": "Sleep", "category": "rest", "essential": True}])},
            "request": REQUEST}

def test_valid_plan_passes():
    v = mp._validate(plan(), REQUEST)
    assert v.valid and v.errors == [] and "commitments" in v.checks

def test_overlap_is_reported_with_a_json_path():
    p = plan(); p["routine"]["blocks"][1]["start"] = "07:15"
    v = mp._validate(p, REQUEST)
    assert not v.valid
    assert any(e.code == "overlap" and e.path == "$.routine.blocks[1]" for e in v.errors)

def test_block_over_a_commitment_is_rejected_unless_it_is_the_commitment():
    p = plan(); p["routine"]["blocks"][0]["start"] = "08:45"
    v = mp._validate(p, REQUEST)
    assert any(e.code == "commitment" for e in v.errors)

def test_text_json_is_accepted():
    assert mp._validate(json.dumps(plan()), REQUEST).valid

@pytest.mark.asyncio
async def test_server_end_to_end_in_process(tmp_path, monkeypatch):
    monkeypatch.setattr(mp, "STORE", tmp_path)
    async with Client(mp.mcp) as client:                       # no subprocess, no network
        names = {t.name for t in (await client.list_tools()).tools}
        assert names == {"get_plan_contract", "validate_plan", "save_plan"}
        bad = await client.call_tool("save_plan", {"plan": {"format": "x"}, "request": REQUEST})
        assert bad.is_error and "Plan not saved" in bad.content[0].text
        ok = await client.call_tool("save_plan", {"plan": plan(), "request": REQUEST})
        assert ok.structured_content["saved"] is True
        assert (tmp_path / "r1.json").exists()
