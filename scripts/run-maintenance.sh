#!/usr/bin/env bash
# Run the autonomous-maintainer on this machine with your normal Claude Code login.
# No API key: ANTHROPIC_API_KEY is unset for the run, so `claude` uses the account you
# signed in with (`claude` → /login). Docs: docs/maintenance/claude-code.md
#
#   scripts/run-maintenance.sh              maintain origin/main in a throwaway worktree, commit to a local branch
#   scripts/run-maintenance.sh --pr         ... and push the branch and open a pull request (uses `gh`)
#   scripts/run-maintenance.sh --focus links|standards|freshness|all   (default all)
#
# Safety, enforced here and not left to the model:
#   - works in a separate git worktree from origin/main; your working tree is never touched
#   - a run that deletes or renames a file is discarded
#   - edits to .github/workflows are reverted (proposals belong in the report)
#   - fact files changed, or a failing check, make the PR a draft labelled needs-review
#   - never pushes to main; you merge the PR (or the local branch) yourself
set -euo pipefail

PR=0
FOCUS=all
while [ $# -gt 0 ]; do
  case "$1" in
    --pr) PR=1 ;;
    --focus) FOCUS="${2:?--focus needs a value}"; shift ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN   # use the subscription login, never an API key
command -v claude >/dev/null || { echo "claude CLI not found" >&2; exit 1; }

REPO="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
DAY="$(date -u +%F)"
BRANCH="maintenance/${DAY}-$(date -u +%H%M)"
WORK="$(mktemp -d)"
WT="$WORK/janaka-maintenance"
LOG_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/janaka-maintenance"; mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/${DAY}.log"

cleanup() { git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT

git -C "$REPO" fetch --quiet origin main
git -C "$REPO" worktree add --quiet -b "$BRANCH" "$WT" origin/main
cd "$WT"
echo "maintenance run on $BRANCH (worktree $WT)"

PROMPT="Run the scheduled-maintenance skill exactly (focus: ${FOCUS}). You are unattended: nobody can answer
questions. Stay inside the policy tiers; everything else is a proposal in reports/maintenance-${DAY}.md.
Never delete or rename files, never change facts about Janaka, never edit .github/workflows, never run
git commit, git push or gh; this script handles git. Finish with the three-line summary."

set +e
claude -p "$PROMPT" \
  --agent autonomous-maintainer \
  --permission-mode acceptEdits \
  --allowedTools "Read,Edit,Write,Glob,Grep,WebFetch,WebSearch,Bash(python3 scripts/build.py:*),Bash(python3 scripts/validate-site.py:*),Bash(python3 scripts/maintenance-scan.py:*),Bash(python3 -m unittest:*),Bash(node --test:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git checkout --:*),Bash(curl -sI:*),Bash(date:*)" \
  --disallowedTools "Bash(git commit:*),Bash(git push:*),Bash(git rm:*),Bash(rm:*),Bash(gh:*)" \
  > "$LOG" 2>&1
claude_rc=$?
set -e
tail -n 5 "$LOG"
[ $claude_rc -eq 0 ] || echo "warning: claude exited with $claude_rc (log: $LOG)"

# --- guards -------------------------------------------------------------------
if git status --porcelain | awk '$1 ~ /[DR]/' | grep -q .; then
  echo "The run deleted or renamed files; policy forbids it. Discarding the run." >&2
  git status --porcelain | awk '$1 ~ /[DR]/' >&2
  exit 1
fi
if ! git diff --quiet -- .github/workflows; then
  echo "Reverting edits to .github/workflows (proposals belong in the report)."
  git checkout -- .github/workflows
fi
FACTS="$(git diff --name-only -- content/profile.json content/projects.json partials/experience.html \
  partials/certifications.html partials/education.html resume/index.html cv/print/index.html \
  chatbot/config.py .claude/skills/brand-voice/SKILL.md assets/js/i18n.js)"

# --- independent verification ---------------------------------------------------
set +e
python3 scripts/build.py > /dev/null 2>&1;                b=$?
python3 scripts/validate-site.py > "$WORK/validate.txt" 2>&1; v=$?
node --test "tests/js/*.test.mjs" > /dev/null 2>&1;       j=$?
python3 -m unittest discover -s tests/python > /dev/null 2>&1; p=$?
set -e
res() { [ "$1" = 0 ] && echo PASS || echo FAIL; }
CHECKS="| Check | Result |
|---|---|
| build | $(res $b) |
| validate-site | $(res $v) |
| JS tests | $(res $j) |
| Python tests | $(res $p) |"
FAILED=$(( b | v | j | p ))

if [ -z "$(git status --porcelain)" ]; then
  echo "Nothing changed; no branch kept."
  git -C "$REPO" branch -D "$BRANCH" >/dev/null 2>&1 || true
  exit 0
fi
REPORT="reports/maintenance-${DAY}.md"
[ -f "$REPORT" ] || printf '# Maintenance %s\n\nThe run made changes but wrote no report. Review carefully.\n' "$DAY" > "$REPORT"

git add -A
git commit --quiet -m "Maintenance ${DAY}: autonomous upkeep" -m "Report: ${REPORT}"
echo "$CHECKS"
[ -n "$FACTS" ] && printf 'Fact files changed (review before merging):\n%s\n' "$FACTS"

if [ "$PR" = 1 ]; then
  git push --quiet -u origin "$BRANCH"
  BODY="$WORK/body.md"
  {
    cat "$REPORT"
    printf '\n---\n### Checks re-run by scripts/run-maintenance.sh\n%s\n' "$CHECKS"
    [ -n "$FACTS" ] && printf '\n### Fact files changed: review against the brand-voice skill\n```\n%s\n```\n' "$FACTS"
    printf '\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n'
  } > "$BODY"
  gh label create maintenance --color 2F4A6D --description "Autonomous maintenance run" --force >/dev/null
  gh label create needs-review --color B60205 --description "Needs a careful human review" --force >/dev/null
  flags=(--label maintenance)
  if [ "$FAILED" != 0 ] || [ -n "$FACTS" ]; then flags+=(--label needs-review --draft); fi
  gh pr create --base main --head "$BRANCH" --title "Maintenance ${DAY}" --body-file "$BODY" "${flags[@]}"
else
  echo "Committed to local branch $BRANCH. Review: git log -p main..$BRANCH   Merge or delete it when done."
fi
