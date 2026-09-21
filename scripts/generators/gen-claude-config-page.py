#!/usr/bin/env python3
"""Generate academy/modules/2026/FSE/claude-code-configuration.html from content/claude-code-configuration.md."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md2academy import build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "scripts", "generators", "content", "claude-code-configuration.md")
OUT = os.path.join(ROOT, "academy", "modules", "2026", "FSE", "claude-code-configuration.html")
CFG = {
    "title": "Claude Code configuration, top down: CLAUDE.md, settings, hooks, skills, subagents, plugins and context",
    "h1": "Claude Code configuration, top down.",
    "description": "One diagram of how Claude Code is configured, then twelve levels that zoom into it: the two layers, where every file lives and who wins, what loads into context and when, the agent loop and its 33 hooks, a tested guard hook, skills, subagents, plugins, a commands cheat sheet, a five-minute recap and fifteen exam-style questions with an answer key. Checked against Claude Code v2.1.278.",
    "url": "https://janaka.me/academy/modules/2026/FSE/claude-code-configuration.html",
    "badges": ["Claude Code v2.1.278", "CCAR-F Domain 2 and 5", "12 levels, top down", "15 practice questions", "Java anchors"],
    "actions": [("Start with the map", "#level-0-the-whole-picture"), ("Jump to the practice questions", "#level-11-practice"), ("Official docs ↗", "https://code.claude.com/docs/en/features-overview")],
}
build(CFG, SRC, OUT)
