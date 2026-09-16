"""Exercise momentum_planner.py over stdio: contract, validate, save (with elicitation), resource, prompt."""
import asyncio, json, os, shlex, sys
from mcp import types
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

REQUEST = {"requestId": "req-2026-10-05-calm-weekday", "requestVersion": 1, "kind": "routine",
           "goal": "A calmer weekday around my job, with movement and an early night.",
           "timezone": "Europe/Zurich", "startDate": "2026-10-05", "wake": "06:45", "sleep": "22:00",
           "commitments": [{"label": "Work", "days": ["mon", "tue", "wed", "thu", "fri"], "start": "09:00", "end": "17:00"}]}
PLAN = {"format": "daily-momentum-ai-plan", "contractVersion": 1, "requestId": REQUEST["requestId"], "kind": "routine",
        "name": "Calm weekday", "tagline": "Movement before work, an early night.",
        "description": "A weekday built around a 09:00-17:00 job with a walk before it and a quiet evening.",
        "routine": {"blocks": [
            {"start": "06:45", "durationMin": 30, "activity": "Walk", "category": "body", "essential": True},
            {"start": "07:15", "durationMin": 45, "activity": "Breakfast", "category": "nourish", "essential": True},
            {"start": "09:00", "durationMin": 480, "activity": "Work", "category": "work", "essential": True},
            {"start": "18:00", "durationMin": 60, "activity": "Dinner", "category": "nourish", "essential": True},
            {"start": "22:00", "durationMin": 480, "activity": "Sleep", "category": "rest", "essential": True}]},
        "request": REQUEST}
BROKEN = json.loads(json.dumps(PLAN))
BROKEN["routine"]["blocks"][1]["start"] = "08:45"      # breakfast now runs into the Work commitment
BROKEN["routine"]["blocks"][3]["category"] = "food"    # not one of the nine categories

async def on_elicit(*args, **kwargs):
    print("  ↳ server asked:", (args[-1].message if args else kwargs))
    return types.ElicitResult(action="accept", content={"overwrite": True})

async def main():
    cmd = shlex.split(os.environ.get("PLANNER_CMD", f"{sys.executable} momentum_planner.py"))   # or: java -jar java/target/momentum-planner.jar
    server = StdioServerParameters(command=cmd[0], args=cmd[1:])
    async with Client(server, elicitation_callback=on_elicit) as client:
        print("connected to", client.server_info.name, "| protocol", getattr(client, "protocol_version", "?"))
        tools = await client.list_tools()
        for t in tools.tools:
            print(f"tool {t.name:18} read_only={t.annotations.read_only_hint if t.annotations else None}  required={t.input_schema.get('required')}")
        contract = await client.call_tool("get_plan_contract", {})
        print("contract categories:", [c["id"] for c in contract.structured_content["categories"]][:4], "…")
        ok = await client.call_tool("validate_plan", {"plan": PLAN, "request": REQUEST})
        print("valid plan →", ok.structured_content["valid"], "| checks:", ok.structured_content["checks"])
        bad = await client.call_tool("validate_plan", {"plan": json.dumps(BROKEN), "request": REQUEST})
        print("broken plan →", bad.structured_content["valid"])
        for e in bad.structured_content["errors"]:
            print(f"  {e['code']:12} {e['path']:28} {e['message']}")
        refused = await client.call_tool("save_plan", {"plan": BROKEN, "request": REQUEST})
        print("save broken → is_error:", refused.is_error, "|", refused.content[0].text[:80], "…")
        saved = await client.call_tool("save_plan", {"plan": PLAN, "request": REQUEST})
        print("save valid  →", saved.structured_content)
        again = await client.call_tool("save_plan", {"plan": PLAN, "request": REQUEST})
        print("save again  → saved:", again.structured_content["saved"])
        res = await client.read_resource(f"plan://{REQUEST['requestId']}")
        print("resource    →", json.loads(res.contents[0].text)["name"])
        prompts = await client.list_prompts()
        print("prompts     →", [p.name for p in prompts.prompts])
asyncio.run(main())
