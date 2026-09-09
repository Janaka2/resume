---
name: coach
description: Daily or weekly session with the success-coach agent - Tony Robbins-style state check, wins, RPM plan (Result, Purpose, Massive Action) tied to the ninety-day targets in goals/vision.md, and one raised standard. Arguments: "daily" (default), "weekly", "decision <topic>", or "vision" to rebuild the goals file.
---

# /coach

Load `goals/vision.md`. If it still contains `[confirm]` placeholders and the argument is not `vision`, start with `vision` mode for the missing pieces, but keep it to the two or three most important blanks.

## Modes

**daily** (default): run the daily check-in from the `success-coach` agent. Gather evidence first (`git log --since="1 day ago" --oneline --no-merges`, scaffold count), then coach. Output ends with a three-line commitment block:

```
Today's One Thing: …
First action (2 min): …
Done by: … (CET)
```

**weekly**: run the weekly review. Evidence window seven days. Ask whether to update the progress markers in `goals/vision.md`; if yes, edit the `## Ninety-day targets` table and the `## Weekly log` section (append one dated row: wins, misses, standard raised, next week's One Thing).

**decision <topic>**: run the big-decision protocol. Finish with a decision and the first action, and offer to log it under `## Decisions` in the vision file.

**vision**: rebuild or refine `goals/vision.md` through questions, one at a time: ten-year identity, one-year outcome per area, ninety-day targets with numbers and dates, the purpose behind each. Write the file when he confirms.

## Proactive use

Pair with `/loop 24h /coach daily` for a morning ping, or a `/schedule` routine at 06:30 CET on weekdays and `/coach weekly` on Sunday evening. The coach reads the same repo the other agents maintain, so its evidence is real shipped work, not self-report.
