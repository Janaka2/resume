# Claude Code configuration, top down

<!-- lede -->
CLAUDE.md, settings, hooks, skills, subagents, plugins, MCP and the context window, learned from the whole picture down to the last field. Start with one diagram you can redraw from memory; every later section is a zoom into one box of it. Facts follow the official documentation at code.claude.com, checked against Claude Code v2.1.278 on 21 September 2026; re-check version-specific details before an exam. Maps to CCAR-F Domain 2 (Claude Code Configuration and Workflows) and part of Domain 5 (Context Management and Reliability).

<!-- eyebrow: Level 0 · The whole picture -->
## One diagram to hold everything.

Before any detail, the map. Read it top to bottom: where configuration comes from, what it turns into when a session starts, and what happens on every turn. Every later section zooms into one box.

```flow
WHERE IT COMES FROM  (four scopes, widest authority first)
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ORGANIZATION  managed-settings.json · managed CLAUDE.md · managed-mcp.json · agents/ │ IT deploys
│ USER          ~/.claude/: CLAUDE.md · settings.json · rules/ skills/ agents/ · memory│ you, everywhere
│ PROJECT       ./CLAUDE.md · .claude/settings.json · rules/ skills/ agents/ · .mcp.json│ team, in git
│ LOCAL         CLAUDE.local.md · .claude/settings.local.json                          │ you, this repo
└───────────────┬───────────────────────────────────┬──────────────────────────────────┘
                │ text Claude READS (guidance)       │ config the harness APPLIES (enforced)
                ▼                                   ▼
WHAT A REQUEST LOOKS LIKE  (stable first, so the prompt cache works)
┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
│ 1 SYSTEM PROMPT          │  │ 2 PROJECT CONTEXT        │  │ 3 CONVERSATION           │
│ core instructions        │+ │ CLAUDE.md: org → user →  │+ │ your prompts, replies,   │
│ tools (MCP: names only)  │  │ project · unscoped rules │  │ tool results, invoked    │
│ environment, git snapshot│  │ first 200 lines MEMORY.md│  │ SKILL.md bodies          │
└──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘
        settings · permission rules · hooks · modes decide what each turn may DO
                │
                ▼
WHAT HAPPENS ON EVERY TURN  (the agent loop, your hooks at fixed points)
SessionStart ▶ UserPromptSubmit ▶ ┌▶ PreToolUse ▶ permission ▶ tool runs ▶ PostToolUse ┐▶ Stop ▶ SessionEnd
                                  └──────────── repeat until Claude has its answer ◀───┘
                                       tool = Skill   → the full SKILL.md joins this context
                                       tool = Agent   → a SUBAGENT loops in its OWN window, returns a summary
                                       tool = mcp__*  → an MCP SERVER outside Claude Code does the work

PACKAGING  a PLUGIN is one folder shipping skills + agents + hooks + MCP servers, versioned and installable
```

> **Keep this** Everything in Claude Code is one of two things. Text Claude *reads* (CLAUDE.md, rules, memory, skills, a subagent's prompt): guidance it can occasionally drift from. Configuration the harness *applies* (settings, permission rules, hooks, modes): enforced, whatever Claude intends. Plugins only package; MCP servers only connect.

> **Java anchor** CLAUDE.md is the team's coding-standards wiki: developers read it, nothing forces them. Settings, permissions and hooks are Spring Security configuration and servlet filters: the framework applies them whatever the developer intends. MCP is to external tools what JDBC is to databases: one interface, many vendor servers.

### How to study this page

1. Redraw the diagram above from memory. Until you can, do not go on; everything else hangs off it.
2. Each level has the same rhythm: big idea, a Java anchor, the facts, exam traps, a self-check. Answer the self-check out loud before opening it.
3. Finish with the fifteen scenario questions at the end and only then open the answer key.

| Level | Zooms into | After it you can |
|---|---|---|
| Rollout | the whole map, in order | walk a company from nothing to a working team, and say which file goes where |
| 1 | the two columns | say which of the eight pieces is guidance and which is enforced, and which to use for which job |
| 2 | the four scopes | name every file, its scope, and who wins a conflict |
| 3 | the three request boxes | recite the startup order and what survives `/compact` |
| 4 | the loop | place each hook event and predict what an exit code does |
| 5 | one hook | read and adapt a real PreToolUse guard hook |
| 6, 7, 8 | Skill, Agent, Plugin | write each file and explain its fields |
| 9, 10 | commands, recap | pick the right command; revise in five minutes |
| 11, 12 | practice, answers | pass the fifteen questions and explain every distractor |

<!-- eyebrow: Rollout · A company, step by step -->
## From an empty laptop to a team shipping with Claude Code.

The map shows what exists. This workbench shows the order in which a company creates it, who does each step, and
exactly where every file lives. Alpine Bank’s payments-portal team is fictional; the files are real, working examples
you can copy. Walk the ten steps with the buttons, click any file in the tree to read it, then place the files
yourself in the exercise below.

> **Big idea** Set up top down, in the same order as the scopes: the organization floor first (IT), then the project
> (tech lead, one pull request), then each person’s own layer. Enforced things (settings, hooks) before guidance
> (CLAUDE.md, skills). Only then does the daily loop start, and the pipeline stays the gate it always was.

<!-- include: claude-code-workbench.html -->

> **Keep this** Ten steps, three owners. IT: managed-settings.json, managed CLAUDE.md, managed-mcp.json. Tech lead:
> /init, .claude/settings.json, hooks, folder CLAUDE.md files and path rules, skills, agents, .mcp.json, all through
> one pull request. Each person: ~/.claude/ for every repo, settings.local.json and CLAUDE.local.md for this one.

<!-- eyebrow: Level 1 · Two layers, eight pieces -->
## Guidance versus enforcement, and which piece for which job.

> **Big idea** Sort every feature into one of two columns first. If you need something to *always* or *never* happen, it must live in the enforced column. If it is know-how, it lives in the guidance column and costs context.

| Claude reads it (guidance) | The harness applies it (enforced) |
|---|---|
| CLAUDE.md files and rules | settings.json: permissions, env, model, plugins |
| Auto memory (MEMORY.md) | managed-settings.json: organization policy |
| Skills: description always, body on use | Permission rules: allow, ask, deny |
| A subagent's prompt, in its own context window | Hooks: your scripts at lifecycle events |
| Output style, part of the system prompt | Permission modes: default, acceptEdits, auto, plan, … |

Two more words complete the vocabulary. A **plugin** bundles skills, agents, hooks and MCP servers into one installable unit. An **MCP server** gives Claude external tools and data.

### The eight building blocks

| Piece | Lives in | Enters Claude's context | Triggered by | Create with |
|---|---|---|---|---|
| **CLAUDE.md + rules** | `CLAUDE.md`, `.claude/rules/*.md` | Full text every session. Subfolder files and path-scoped rules when Claude reads matching files. | Automatic | `/init`, then edit (or `/memory`) |
| **Auto memory** | `~/.claude/projects/<repo>/memory/MEMORY.md` | First 200 lines or 25 KB, every session | Claude writes it itself | Automatic; toggle in `/memory` |
| **Skill** | `skills/<name>/SKILL.md` + extra files | Name and description always; full body only when used | You (`/name`) or Claude (description match) | Create the folder, or ask Claude |
| **Subagent** | `agents/<name>.md` | Only its description. It works in its own window and returns a summary. | The main session's Agent tool | Ask Claude, or write the file |
| **Hook** | `"hooks"` key in `settings.json` | Nothing, unless it returns output | Claude Code, at lifecycle events | Edit the JSON, or ask Claude |
| **Settings** | `settings.json`, `settings.local.json`, `managed-settings.json` | Nothing; they configure the harness | Read at startup, reloaded on save | `/config`, "don't ask again" approvals, or edit |
| **MCP server** | `.mcp.json`, `~/.claude.json` | Tool names at start; full schemas when needed | Claude calls its tools | `claude mcp add --scope project` |
| **Plugin** | `.claude-plugin/plugin.json` + folders | Whatever it bundles, prefixed like `plugin:skill` | Switched on via `enabledPlugins` | `/plugin` to install; `claude plugin init <name>` |

### Which piece for which job

| You need | Use | Because |
|---|---|---|
| Rules for every task: build commands, conventions | **CLAUDE.md** | loaded in full every session |
| Know-how for some tasks: runbooks, checklists | **Skill** | costs tokens only when used |
| To isolate noisy work: big reviews, research | **Subagent** | own context; only a summary returns |
| To guarantee something always or never happens | **Hook or permission rule** | enforced by the harness, not by Claude |
| To reach an external system | **MCP server** | gives Claude tools it can call |
| To share all of the above | **Plugin** | one versioned, installable package |

> **Memory hook: ALON** When does it load? **A**lways: CLAUDE.md files, unscoped rules, the first 200 lines of MEMORY.md. **L**isted: skill and subagent descriptions, MCP tool names. **O**n use: full SKILL.md, path-scoped rules, nested CLAUDE.md, MCP tool schemas. **N**ever in the main context: settings, hooks, a subagent's own work (only its summary comes back). Read it as "alone": the less that loads, the less Claude carries.

### Seven myths, fixed

| Myth | Reality |
|---|---|
| "Settings are XML." | They are JSON: `settings.json`. The organization file is `managed-settings.json`. |
| "`/init` writes `.claude/CLAUDE.md`." | It writes `./CLAUDE.md` at the project root (`./.claude/CLAUDE.md` also works). If one exists, `/init` suggests improvements instead. |
| "Skills live in one skills.md." | One folder per skill: `.claude/skills/<name>/SKILL.md`. |
| "Proactive subagents start themselves." | The main session, or a parent subagent up to three levels deep, always launches them through the Agent tool. "Use proactively" only makes delegation more eager. |
| "`/agents` creates agents." | The `/agents` wizard was removed in v2.1.198. Ask Claude, or write the file. |
| "`/hooks` edits hooks." | `/hooks` is a read-only browser. Edit `settings.json`, or ask Claude. |
| "CLAUDE.md rules are enforced." | CLAUDE.md is guidance. Only settings, permission rules and hooks enforce. |

::: quiz Check yourself: level 1
- Which two things are in Claude's context in full from the very first message?
- Who launches a subagent, and through which tool?
- Where does `/init` write CLAUDE.md?
- You must guarantee a command never runs. Which pieces can do that?
Answers:
- CLAUDE.md files (with unscoped rules) and the first 200 lines or 25 KB of MEMORY.md.
- The main session, or a parent subagent, through the Agent tool.
- `./CLAUDE.md` at the project root.
- A permission deny rule or a hook. Not CLAUDE.md.
:::

<!-- eyebrow: Level 2 · Where every file lives -->
## Four scopes, one precedence chain, and how an organization enforces policy.

> **Big idea** Four scopes, from widest authority to most personal: Organization (managed by IT) → User (`~/.claude`, all your projects) → Project (the repo, shared through git) → Local (you, this repo only, git-ignored).

> **Java anchor** Spring Boot externalized configuration: several property sources merged by precedence. The difference is that the organization layer sits on top and cannot be overridden, like a bank-wide security baseline pushed by group policy.

### The file map

```flow
ORGANIZATION: IT deploys it, you can't override it
  macOS    /Library/Application Support/ClaudeCode/
  Linux    /etc/claude-code/
  Windows  C:\Program Files\ClaudeCode\
  ├── managed-settings.json      permissions, locks, env, allowed plugins
  ├── managed-settings.d/*.json  optional drop-ins, merged alphabetically
  ├── managed-mcp.json           MCP servers the org provides or restricts
  ├── CLAUDE.md                  org-wide instructions (can't be excluded)
  └── .claude/agents/            org-wide subagents
  (or delivered via MDM/registry, or the claude.ai admin console)

USER: ~/  (you, every project, never committed)
  ├── .claude.json               app state: login, folder trust, your MCP servers
  └── .claude/
      ├── CLAUDE.md              your personal instructions
      ├── settings.json          your permissions, hooks, env, model, plugins
      ├── rules/  skills/  agents/  commands/  output-styles/
      ├── projects/<repo>/memory/MEMORY.md    auto memory (Claude writes it)
      ├── projects/<repo>/*.jsonl             session transcripts
      └── plugins/               installed plugins + marketplaces

PROJECT: ~/pro/  (team, commit to git)
  ├── CLAUDE.md                  ← /init creates this
  ├── CLAUDE.local.md            LOCAL: your private notes; add to .gitignore
  ├── AGENTS.md                  read instead, only if no CLAUDE.md exists
  ├── .mcp.json                  team MCP servers
  └── .claude/
      ├── settings.json          team permissions, hooks, env, plugins
      ├── settings.local.json    LOCAL: your overrides (auto-gitignored)
      ├── rules/*.md             topic rules; "paths:" frontmatter = load on match
      ├── skills/<name>/SKILL.md (+ scripts/, reference files)
      ├── agents/<name>.md       subagents
      ├── hooks/*.sh             scripts your hooks call (a convention, not auto-loaded)
      └── commands/  output-styles/  workflows/  agent-memory/   (less common)
```

### Who wins a conflict

| What | Rule | Order, highest first |
|---|---|---|
| **Settings** | Merged key by key. List keys such as `permissions.allow` are combined across files. | managed → `--settings` flag → `.claude/settings.local.json` → `.claude/settings.json` → `~/.claude/settings.json` |
| **CLAUDE.md** | Additive: every level loads. The most specific is read last and usually wins. | managed → user → project, from the filesystem root down to your folder |
| **Skills** (same name) | Override | managed > user > project |
| **Subagents** (same name) | Override | managed > `--agents` flag > project > user > plugin |
| **MCP servers** (same name) | Override | local > project > user |
| **Hooks** | Merge: every matching hook runs | An organization can allow managed hooks only |

> **Memory hook** Settings order M-C-L-P-U: "My Cat Likes Purple Umbrellas" = Managed, CLI, Local, Project, User.

> **Exam traps** Skills and subagents break user-versus-project ties in opposite directions: a personal skill beats a project skill, but a project subagent beats a personal one. `~/.claude.json` (app state, folder trust, your MCP servers) is a different file from `~/.claude/settings.json`. A managed CLAUDE.md is only guidance; the technical lock is managed settings. `CLAUDE.local.md` and `settings.local.json` are personal: keep them out of git (`settings.local.json` is git-ignored automatically).

### Enforcing policy for an organization

- **Three delivery channels.** A `managed-settings.json` file in the system folder (plus `managed-settings.d/*.json` drop-ins, merged alphabetically); OS policy via MDM (macOS plist domain `com.anthropic.claudecode`, Windows registry `HKLM\SOFTWARE\Policies\ClaudeCode`); or server-managed settings from the claude.ai admin console.
- **System folders.** macOS `/Library/Application Support/ClaudeCode/`; Linux and WSL `/etc/claude-code/`; Windows `C:\Program Files\ClaudeCode\`.
- **Useful locks.** `permissions.deny` rules, `allowManagedHooksOnly`, `allowManagedPermissionRulesOnly`, and `strictPluginOnlyCustomization`, which blocks skills, agents, hooks and MCP servers from user and project sources.
- **Also managed.** `managed-mcp.json` for MCP servers, a managed CLAUDE.md for behavioural guidance, and `.claude/agents/` in the managed folder for org-wide subagents.

::: quiz Check yourself: level 2
- Managed settings deny `Bash(sudo *)`; your `settings.local.json` allows it. What happens?
- A personal and a project skill are both called `deploy`. Which runs? And if they were subagents?
- Name the three ways to deliver managed settings.
- Two CLAUDE.md files give conflicting instructions. Which applies?
Answers:
- Denied: managed settings win.
- Skill: the personal one. Subagent: the project one.
- A `managed-settings.json` file (with `.d` drop-ins), MDM or registry policy, or server-managed settings from the admin console.
- Both load; Claude usually follows the more specific one, which is read last.
:::

<!-- eyebrow: Level 3 · What loads, and when -->
## The three request layers, the startup order, and what survives /compact.

> **Big idea** Every request is built in three layers, most stable first, so the prompt cache can reuse the front of it: System prompt → Project context → Conversation.

> **Java anchor** Startup configuration versus request scope. CLAUDE.md is bound once at startup, like `@ConfigurationProperties` without `@RefreshScope`: an edit needs a "restart" (`/clear`, `/compact` or a new session). Settings files, by contrast, are watched and hot-reloaded.

```flow
 ┌─ SYSTEM PROMPT (cached prefix) ──────────────────────────────────────────────────────┐
 │ 1 core instructions (+ output style, + --append-system-prompt)                       │
 │ 2 tool definitions: Read, Edit, Bash, Grep, Agent, Skill…   MCP tools: names only    │
 │ 3 environment: cwd, platform, shell, OS, git repo?, auto-memory paths                │
 │ 4 git snapshot: branch, status, recent commits          ← taken ONCE, at startup     │
 ├─ PROJECT CONTEXT (a user message after the system prompt) ───────────────────────────┤
 │ 5 managed CLAUDE.md                                                                  │
 │ 6 ~/.claude/CLAUDE.md, then ~/.claude/rules/            user rules load first,       │
 │ 7 project CLAUDE.md files, root → your folder;            so project rules win       │
 │   in each folder CLAUDE.md then CLAUDE.local.md; unscoped rules; @imports (4 hops)   │
 │ 8 auto memory: first 200 lines / 25 KB of MEMORY.md                                  │
 │ – skill listing, subagent descriptions, SessionStart hook output (position undocumented) │
 ├─ CONVERSATION ───────────────────────────────────────────────────────────────────────┤
 │ your prompts · replies · tool results · invoked SKILL.md bodies · plan mode          │
 │ path-scoped rules and nested CLAUDE.md when a matching file is read                  │
 │ MCP tool schemas when a specific tool is needed                                      │
 └──────────────────────────────────────────────────────────────────────────────────────┘
```

### Startup order, as a table

| # | Layer | What loads |
|---|---|---|
| 1 | System prompt | Claude Code's core instructions (not published). An output style replaces the default software-engineering instructions unless it sets `keep-coding-instructions: true`. Any `--append-system-prompt` text is added. |
| 2 | System prompt | Built-in tool definitions (Read, Edit, Bash, Grep, Agent, Skill, …). MCP tools are deferred: names only, full schemas when needed. |
| 3 | System prompt | Environment: working directory, platform, shell, OS version, whether it is a git repo, and your auto-memory paths. |
| 4 | System prompt | A git snapshot at the very end: branch, status, recent commits. Taken once at startup. |
| 5 | Project context | Managed (organization) CLAUDE.md. |
| 6 | Project context | `~/.claude/CLAUDE.md`, then `~/.claude/rules/`. User rules load before project rules, so project rules win. |
| 7 | Project context | Project CLAUDE.md files from the filesystem root down to your folder; in each folder CLAUDE.md, then CLAUDE.local.md. Rules without paths load with `.claude/CLAUDE.md` priority. `@imports` expand (max 4 hops); HTML comments are stripped. No CLAUDE.md anywhere? `AGENTS.md` is read instead. |
| 8 | Project context | Auto memory: the first 200 lines or 25 KB of MEMORY.md. |
| – | Before your first prompt | The skill listing (model-invocable skills only), subagent descriptions, and SessionStart hook output. Their exact position is not documented. |

The project-context layer is sent as a **user message after the system prompt**, not inside it.

### During the conversation

- Full SKILL.md bodies and plan mode are **appended as messages**, so the cached prefix stays intact.
- Path-scoped rules and nested CLAUDE.md files load when Claude reads a matching file.
- MCP tool schemas load when Claude needs a specific tool.
- **Never loaded until needed:** user-only skills (until you type `/name`), a skill's supporting files, auto-memory topic files, and CLAUDE.md in `--add-dir` folders.

### After /compact

| Item | What happens |
|---|---|
| System prompt | Stays |
| Project-root CLAUDE.md, unscoped rules, auto memory | Re-read from disk and re-injected |
| Skills you invoked | Re-injected, capped at 5,000 tokens each (25,000 total) |
| Recently modified files | Up to 5 re-read |
| **Skill listing** | **Not re-injected** |
| Path-scoped rules, nested CLAUDE.md | Only when a matching file is read again |

### A subagent's own stack

Its own system prompt (which replaces Claude Code's; only environment details are added), plus CLAUDE.md files (not for the built-in Explore and Plan agents), plus preloaded skills, plus a git status snapshot, plus the task Claude wrote for it. **Not** your conversation, and **not** your main auto memory.

> **Memory hook** S → P → C: "Stable first, Chatty last." System prompt, Project context, Conversation.

> **Exam traps** Editing CLAUDE.md mid-session has no effect until `/clear`, `/compact` or a restart; settings and agent files hot-reload. The skill listing does not survive `/compact`, only skills you actually invoked do. CLAUDE.md is delivered as a user message after the system prompt, not inside it. A subagent never sees your conversation, only the task it was given. Verify in a real session: `/context` shows the live breakdown, including which memory files loaded; `/status` shows the active settings sources.

::: quiz Check yourself: level 3
- You edit CLAUDE.md mid-session. When does Claude see the change?
- Is the git status in context refreshed during the session?
- Which startup item is not re-injected after `/compact`?
- Name the three request layers in order.
Answers:
- After `/clear`, `/compact` or a restart.
- No, it is a snapshot taken at startup.
- The skill listing.
- System prompt → project context → conversation.
:::

<!-- eyebrow: Level 4 · The loop and its hooks -->
## Where each hook event fires, what a hook can do, and why exit codes matter.

> **Big idea** Hooks are your code at fixed points of the agent loop. They run outside the model, deterministically, and can allow, block, rewrite or add context.

> **Java anchor** Servlet filters and Spring `HandlerInterceptor`s around the agent loop. PreToolUse ≈ `preHandle` (can reject the call). PostToolUse ≈ `postHandle` (cannot undo, can report). SessionStart ≈ `ApplicationReadyEvent`. SessionEnd ≈ `@PreDestroy`.

```flow
   ① session starts ──────────── SessionStart ──── inject context via stdout
          │
   ② you send a prompt ────────── UserPromptSubmit ─ block it, or add context
          │
   ┌──────▼───────────────────────────────────────────────────────────────────────┐
   │ ③ Claude calls a tool ─────── PreToolUse ────── allow · deny · ask · edit input │
   │ ④ permission check ────────── PermissionRequest  approve or deny for the user   │
   │ ⑤ tool runs, result returns ─ PostToolUse ────── format, lint, feed errors back │   ↻ repeats until
   │        tool = Skill  → full SKILL.md joins the context                           │     Claude has
   │        tool = Agent  → subagent loop, wrapped by SubagentStart / SubagentStop    │     its answer
   └──────┬───────────────────────────────────────────────────────────────────────┘
   ⑥ Claude finishes its reply ─ Stop ──────────── block it: Claude keeps working
          │
   ⑦ session ends ────────────── SessionEnd ─────── cleanup, logging (cannot block)
   any time: PreCompact · PostCompact · Notification
```

### All 33 hook events

| Group | Events |
|---|---|
| Session | SessionStart, Setup, SessionEnd |
| Prompt | UserPromptSubmit, UserPromptExpansion |
| Tools | PreToolUse, PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch |
| End of turn | Stop, StopFailure |
| Subagents and teams | SubagentStart, SubagentStop, TaskCreated, TaskCompleted, TeammateIdle |
| Context and config | InstructionsLoaded, ConfigChange, PreCompact, PostCompact, PreModelSwitch, PostModelSwitch |
| Files and workspace | CwdChanged, DirectoryAdded, FileChanged, WorktreeCreate, WorktreeRemove |
| UI and MCP | Notification, MessageDisplay, Elicitation, ElicitationResult |

`Setup` fires for `claude --init-only` (or `--init` / `--maintenance` with `-p`). It has nothing to do with the `/init` command.

### Anatomy of a hook

Event, optional matcher, handler:

```json
"hooks": {
  "PreToolUse": [                                  // ← event
    {
      "matcher": "Bash",                           // ← which tool; a regex like "Edit|Write" or "mcp__github__.*"
      "hooks": [
        { "type": "command",                       // ← handler: command | http | mcp_tool | prompt | agent
          "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-dangerous.sh",
          "args": [], "timeout": 10 }
      ]
    }
  ]
}
```

| Where a hook can live | Active when |
|---|---|
| Any settings file: user, project, local, managed | The whole session, and also inside subagents |
| A plugin's `hooks/hooks.json` | While the plugin is enabled, and also inside subagents |
| A subagent's frontmatter (`hooks:`) | Only while that subagent runs (Stop becomes SubagentStop) |
| A skill's frontmatter (`hooks:`) | From the skill's first use until the session ends |

| Handler type | What runs |
|---|---|
| `command` | A shell command; the event JSON arrives on stdin |
| `http` | The event JSON is POSTed to a URL |
| `mcp_tool` | An MCP tool is called |
| `prompt` | A one-turn model evaluation decides |
| `agent` | A subagent that can read files before deciding |

### What the exit code means

| Exit code | Meaning | Effect |
|---|---|---|
| **0** | Proceed | JSON on stdout is parsed. For SessionStart and UserPromptSubmit, plain stdout becomes context. |
| **2** | Block | Blocks events that can block: PreToolUse stops the call, UserPromptSubmit rejects the prompt, Stop makes Claude continue. stderr becomes the reason. |
| **Anything else, including 1** | Non-blocking error | The action **goes ahead**. |

JSON output (exit 0 plus JSON on stdout):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",              // allow | deny | ask
    "permissionDecisionReason": "Recursive delete of ~ ..."
  }
}
```

Other fields: `updatedInput` rewrites the tool call, `additionalContext` adds text Claude sees, `continue: false` stops everything, `systemMessage` shows a message to the user.

> **Memory hook** 0 = go, 2 = no, anything else = shrug. And silence is not a "yes".

> **Exam traps** Exit 1 never blocks. A policy hook must exit 2 or return a JSON deny. A hook that times out, or whose script path is wrong or not executable, is a non-blocking error: the gate is silently off. Exit 0 with no output is not approval; the normal permission flow still decides. For a fixed hard rule, a `permissions.deny` entry is the most reliable lock; use hooks when the decision needs logic. `/hooks` only displays hooks. Settings, managed and plugin hooks already fire inside subagents; do not repeat them in subagent frontmatter.

::: quiz Check yourself: level 4
- Your guard hook exits 1 on `rm -rf ~`. What happens?
- Which event would auto-format files after Claude edits them?
- Which event can stop Claude from ending its turn?
- Which handler type lets a model make the decision?
Answers:
- The command runs: exit 1 is non-blocking.
- PostToolUse with matcher `Edit|Write`.
- Stop (block → Claude continues).
- `prompt` (or `agent`, if it needs to read files first).
:::

<!-- eyebrow: Level 5 · Worked example -->
## A real PreToolUse guard hook, tested against 66 commands.

> **Big idea** Deny the catastrophic, ask before the risky, stay silent for everything else, and pair the hook with a `permissions.deny` floor.

> **Java anchor** A web application firewall in front of a payment API: a deny list, step-up approval for risky operations, pass-through for normal traffic. Pattern matching can be bypassed, so it complements authorization (permission rules) rather than replacing it.

### What it decides

| Decision | Examples | Effect |
|---|---|---|
| **Deny** | `rm -rf` on `/`, `~`, `$HOME`, `.`, `..`, `*` or system folders; curl or wget piped into a shell; `mkfs`; `dd` onto a device; disk erase; `find -delete` across `/` or `~`; fork bomb | Blocked. Claude sees the reason and picks a safer route. |
| **Ask** | `git push --force`, `git reset --hard`, `git clean -f`, `terraform destroy`, `kubectl delete`, `DROP` or `TRUNCATE`, `chmod -R 777` | You approve or reject. |
| **Silent** | Everything else, such as `npm test` or `rm -rf node_modules` | Your normal permission rules decide. |

### How it works

- Reads the event JSON from stdin with `jq`, then lowercases and normalises the command.
- Splits compound commands (`;`, `&&`, `|`, `$(…)`, backticks) and strips wrappers (`sudo`, `env`, `bash -c`, `xargs`, …), so each simple command is checked on its own.
- Prints a JSON `permissionDecision` (deny beats ask), or nothing for "no opinion".
- Fails **closed** on its own errors: missing `jq` or unreadable input → exit 2.
- Fails **open** on setup errors: wrong path or missing `chmod +x` → Claude Code treats it as a non-blocking error.

### The settings that wire it in

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "deny": ["Bash(sudo *)"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-dangerous.sh",
            "args": [],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

The `sudo` deny rule is the hard floor for a fixed pattern. The hook adds judgement a fixed rule cannot express: `rm -rf build/` is fine, `rm -rf ~` is not.

### Install and test

```bash
cd ~/pro
mkdir -p .claude/hooks
cp ~/Downloads/block-dangerous.sh .claude/hooks/
chmod +x .claude/hooks/block-dangerous.sh
echo '{"tool_input":{"command":"rm -rf ~"}}' | .claude/hooks/block-dangerous.sh   # prints a deny decision
echo '{"tool_input":{"command":"npm test"}}'  | .claude/hooks/block-dangerous.sh   # prints nothing
```

Then run `/hooks` in Claude Code: the hook should appear under PreToolUse, labelled Project Settings.

::: fold The full script: block-dangerous.sh (shellcheck-clean)
```bash
#!/usr/bin/env bash
# .claude/hooks/block-dangerous.sh
#
# PreToolUse hook for Claude Code's Bash tool.
# Reads the hook event JSON on stdin and answers with one of:
#   deny        -> the command is blocked and Claude is told why
#   ask         -> you get a permission prompt, even if a rule would allow it
#   (no output) -> no opinion; your normal permission rules decide
#
# Pattern matching is best effort: a seatbelt against accidents,
# not a security boundary. Requires jq.
set -uo pipefail

# Fail closed: without jq the command can't be inspected, so block it.
if ! command -v jq >/dev/null 2>&1; then
  echo "block-dangerous.sh: jq is not installed (brew install jq / apt install jq). Bash is blocked until it is." >&2
  exit 2
fi
cmd=$(jq -r '.tool_input.command // empty') || {
  echo "block-dangerous.sh: could not parse the hook input." >&2
  exit 2
}
[ -z "$cmd" ] && exit 0

# Normalise: join line continuations, turn newlines into ';',
# lowercase everything and squeeze whitespace to single spaces.
cmd=${cmd//$'\\\n'/ }
lc=$(printf '%s' "$cmd" | tr '\n' ';' | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')

verdict="" reason=""
flag() {   # flag deny|ask "reason"   (deny beats ask; first reason wins)
  case "$verdict:$1" in
    deny:*|ask:ask) ;;
    *) verdict=$1 reason=$2 ;;
  esac
}
check() {  # check deny|ask 'regex' "reason"   (tested against the current segment $s)
  if [[ $s =~ $2 ]]; then flag "$1" "$3"; fi
}

# ---- Checks on the whole command (these span pipes) -------------------------
re_pipe_shell='(curl|wget).*\| *(sudo +)?(ba|z|da|k)?sh( |$)|(ba|z|da|k)?sh <\( *(curl|wget)'
re_forkbomb=':\(\) *\{ *:\|:'
[[ $lc =~ $re_pipe_shell ]] && flag deny "Piping a downloaded script into a shell. Download it first, show the user what it does, then run it."
[[ $lc =~ $re_forkbomb ]] && flag deny "Fork bomb."

# ---- Checks per simple command ----------------------------------------------
# Split on ; & | ( ) and backticks, so "cd x && rm -rf ~" and "$(rm -rf /)"
# are each checked on their own.
segments=$(printf '%s\n' "$lc" | sed 's/[;&|()`]/\n/g')

# Wrappers and shell keywords to peel off the front: VAR=x, sudo, env, xargs -0, bash -c, then ...
re_prefix='^([a-z_][a-z0-9_]*=[^ ]*|sudo|doas|env|command|builtin|exec|eval|nohup|nice|time|xargs|if|then|else|elif|do|while|until|!|\{|(ba|z|da|k)?sh -c|-[a-z0-9-]+) '
re_rm='^([^ ]*/)?rm '
re_recursive=' (-[a-z]*r[a-z]*|--recursive)( |$)'
re_target=' (/|~|\$home|\$\{home\}|\.|\.\.|\*|/(applications|bin|boot|dev|etc|home|lib|library|opt|root|sbin|system|users|usr|var))(/?\*|/)?( |$)'

while IFS= read -r s; do
  s=${s//\"/}; s=${s//\'/}        # rm -rf "/" is the same as rm -rf /
  s=${s# }
  while [[ $s =~ $re_prefix ]]; do s=${s#"${BASH_REMATCH[0]}"}; done
  [ -z "$s" ] && continue

  # DENY: irreversible, never OK from an agent
  if [[ $s =~ $re_rm && $s =~ $re_recursive && $s =~ $re_target ]]; then
    flag deny "Recursive delete of /, ~, \$HOME, ., .., * or a system folder. Delete specific paths instead, e.g. rm -rf build/."
  fi
  check deny '^find (/|~|\$home)( |$).*-delete'             "find -delete across / or the home folder."
  check deny '^mkfs'                                          "Formatting a filesystem."
  check deny '^dd .*of=/dev/'                                 "Writing raw bytes to a device."
  check deny '^diskutil (erase|zero|secureerase|partition)'   "Erasing or repartitioning a disk."
  check deny '> ?/dev/(sd|hd|vd|xvd|nvme|disk)'               "Redirecting output onto a raw disk."

  # ASK: sometimes legitimate, so a human decides
  check ask '^git push( .*)? (-f|--force[a-z-]*|\+[^ ]+)( |=|$)'  "Force push rewrites shared history."
  check ask '^git reset( .*)? --hard( |$)'                        "git reset --hard throws away uncommitted work."
  check ask '^git clean( .*)? -[a-z]*f'                           "git clean -f deletes untracked files."
  check ask '^terraform (destroy|apply( .*)? -auto-approve)'      "Changes or destroys infrastructure without review."
  check ask '^kubectl delete '                                    "Deletes Kubernetes resources."
  check ask '^chmod (-r|--recursive) ([^ ]+ )*(777|a\+rwx)'       "Makes files world-writable, recursively."
  check ask '(^| )(drop (table|database|schema)|truncate table)( |$)' "Destructive SQL."
done <<< "$segments"

# ---- Answer ------------------------------------------------------------------
[ -z "$verdict" ] && exit 0      # silent = no opinion
[ "$verdict" = deny ] && reason="$reason If it is truly needed, ask the user to run it themselves."
jq -n --arg d "$verdict" --arg r "block-dangerous hook: $reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: $d,
    permissionDecisionReason: $r
  }
}'
```
:::

> **Limits to remember** It is pattern matching: a seatbelt against accidents, not a security boundary. A deliberately disguised command can get past it. Run the two-line test once: a setup mistake silently disables the gate. Needs `jq`. Works on macOS, Linux and WSL; the hooks reference has a PowerShell version for native Windows.

::: quiz Check yourself: level 5
- Why does the script print JSON for "ask" cases instead of exiting 2?
- What happens if you forget `chmod +x`?
- Why keep the `Bash(sudo *)` deny rule when the hook exists?
Answers:
- Exit 2 can only block; "ask" needs the JSON `permissionDecision`.
- The hook cannot start → non-blocking error → commands run unchecked.
- Deny rules are the most reliable lock for a fixed pattern; hooks can fail open.
:::

<!-- eyebrow: Level 6 · Skills -->
## Know-how that costs almost nothing until it is used.

> **Big idea** A skill is a folder of instructions, plus optional scripts and reference files. Its description is always listed; its body loads only when it is used.

> **Java anchor** A `@Lazy` bean: the definition (name and description) is registered at startup, and the full bean is created only on first use.

| Aspect | Rule |
|---|---|
| File | `skills/<name>/SKILL.md`: frontmatter (`name`, `description`), then instructions. Extra files sit beside it. |
| Where | `~/.claude/skills/` (personal), `.claude/skills/` (project), a plugin's `skills/` (as `plugin:skill`), managed |
| In context | Name and description always; full body when invoked; supporting files only when read |
| Invoked by | Claude, when the description matches the task, or you, by typing `/name` |
| User-only | `disable-model-invocation: true` → not listed, zero cost until you type `/name`, and cannot be preloaded into subagents |
| Commands | `.claude/commands/*.md` is the older, single-file form of the same mechanism |
| Name clash | managed > user > project |
| Hooks in frontmatter | Active from the skill's first use until the session ends |
| After `/compact` | The listing is gone; invoked bodies are re-injected (capped) |
| In subagents | The `skills:` field preloads full content. With `Skill` in its tools, a subagent can invoke other skills. |

### Example frontmatter

```markdown
---
name: review-checklist
description: Checklist for reviewing code changes - correctness, security, tests and maintainability. Use when reviewing a diff, a pull request or a commit.
---
# Code review checklist
Work through every section for each changed file. Report only real findings.
...
```

::: fold The full review-checklist skill
```markdown
---
name: review-checklist
description: Checklist for reviewing code changes - correctness, security, tests and maintainability. Use when reviewing a diff, a pull request or a commit.
---
# Code review checklist

Work through every section for each changed file. Report only real findings, not ticked boxes.

## Correctness
- Edge cases: empty, null, zero, very large, unicode, time zones
- Errors handled at the right level; nothing swallowed silently
- Concurrency: shared state, thread safety, retries that are safe to repeat
- Resources closed on every path (connections, streams, files)

## Security
- Input validated at every trust boundary
- No SQL, shell commands or file paths built from untrusted input
- Authorization checked on every endpoint and service call, not only authentication
- No secrets, tokens or personal data in code, logs or error messages
- No untrusted data into deserialization, reflection or templates

## Tests
- New behaviour is tested, including the failure path
- Tests assert outcomes, not implementation details
- No test depends on ordering, the clock or the network without a stub

## Maintainability
- Names say what things are; no dead or commented-out code
- Each function does one thing; duplication extracted
- Public API changes are backward compatible, or flagged as breaking
```
:::

> **Exam traps** A skill adds instructions to the current context; a subagent works in a separate one. Loading a big skill isolates nothing. The description is what Claude matches on: a vague description means the skill never fires. Personal beats project for skills, the opposite of subagents.

::: quiz Check yourself: level 6
- What does a skill cost in context before it is used?
- How do you make a skill that only you can trigger?
- Skill or CLAUDE.md for a 3,000-line runbook used once a month?
Answers:
- Its name and description in the listing.
- Set `disable-model-invocation: true`.
- Skill: it costs tokens only when used.
:::

<!-- eyebrow: Level 7 · Subagents -->
## Specialists with their own context window: the definition file and all 18 fields.

> **Big idea** A subagent is a specialist with its own context window, system prompt and tool limits. The main session delegates through the Agent tool and gets back only a summary.

> **Java anchor** Calling a downstream microservice with its own bounded context: you send a request DTO (the task), it works with its own state and permissions, and it returns a response DTO (the summary). It never sees your session.

### How it is invoked

- **Automatically**, when your request matches its description. "Use proactively…" makes this eager.
- **Explicitly**: `@"code-reviewer (agent)" review my changes`.
- **As the whole session**: `claude --agent code-reviewer`, which also sends its `initialPrompt`.
- Subagents can launch their own subagents, up to three levels deep by default. In interactive sessions they run in the background by default.
- **Where**: `.claude/agents/` (project), `~/.claude/agents/` (user), a plugin's `agents/`, managed, the `--agents` flag. Edits hot-reload within seconds; restart only after the first file in a brand-new agents folder.

### Example: .claude/agents/code-reviewer.md

```markdown
---
name: code-reviewer
description: Reviews code changes for bugs, security issues and maintainability problems. Use proactively after writing or modifying code, and before every commit.
tools: Read, Grep, Glob, Bash
model: sonnet
effort: high
maxTurns: 25
skills:
  - review-checklist
memory: project
color: purple
initialPrompt: Review the current changes and give your verdict.
---
You are a senior code reviewer. You review code; you never modify it.

When invoked:
1. Run `git status` and `git diff HEAD` to see uncommitted changes. If there are none,
   review the branch against the default branch instead (e.g. `git diff main...HEAD`).
   If the task names specific files, focus on those.
2. Read each changed file and enough surrounding code to understand it.
3. Check your agent memory for this codebase's conventions and recurring issues.

Review for:
- Correctness: logic errors, edge cases, null handling, concurrency, error handling
- Security: injection, missing authorization checks, secrets in code, unsafe deserialization
- Maintainability: naming, duplication, complexity, missing or weak tests

Report findings grouped as Critical (must fix), Warnings (should fix) and Suggestions.
For each finding give file:line, the problem, and a concrete fix.
End with a one-line verdict: APPROVE or REQUEST CHANGES.

Before you finish, add any new recurring pattern or convention you noticed to your agent memory.
```

Everything below the second `---` is the agent's **entire system prompt**: it replaces Claude Code's own. Only `name` and `description` are required.

### Fields used in the example

| Field | What it does | Watch out |
|---|---|---|
| `name` (required) | The agent's ID: lowercase letters and hyphens. What you @-mention; hooks see it as `agent_type`. The filename need not match. | A `:` (reserved for plugin agents) or a leading `-` → file skipped silently. Duplicate names in one folder → only one loads, unpredictably. |
| `description` (required) | What Claude matches your request against when deciding to delegate. "Use proactively…" makes it delegate on its own. | Always in the main context. All descriptions together above 15,000 tokens → warning. |
| `tools` | Allowlist. Omit it to inherit every tool available to subagents. Accepts MCP patterns like `mcp__github`. | Nothing resolves → the agent usually will not launch. Preload skills with `skills`, not `Skill`. |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, a full ID like `claude-opus-5`, or `inherit`. | A model passed for one call overrides it. If omitted: `CLAUDE_CODE_SUBAGENT_MODEL`, then your main model. The org's `availableModels` can swap it. |
| `effort` | `low`, `medium`, `high`, `xhigh` or `max` while it runs. | Available levels depend on the model. |
| `maxTurns` | Hard cap on the agent's turns. | At the cap you get partial output; Claude can resume the agent. |
| `skills` | Skills injected in full at startup. | Missing ones are skipped (debug log only). User-only skills cannot be preloaded. |
| `memory` | Notes kept across sessions. `project` → `.claude/agent-memory/<name>/`, `local` → `.claude/agent-memory-local/<name>/`, `user` → `~/.claude/agent-memory/<name>/`. The first 200 lines or 25 KB of its MEMORY.md load each run. | Also turns on Read, Write and Edit, even for an agent meant to be read-only. No effect if auto memory is off. |
| `color` | Colour in the task list and transcript: red, blue, green, yellow, purple, orange, pink, cyan. | Cosmetic. |
| `initialPrompt` | First message sent automatically when the agent runs as the whole session (`claude --agent`). | Only used in that case. |

### The other fields

| Field | What it does | Watch out |
|---|---|---|
| `disallowedTools` | Denylist: inherit every tool except these. Applied before `tools`. | `Bash(git push *)` removes all of Bash. Block single commands with `permissions.deny`. |
| `permissionMode` | `default` (Manual), `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions` or `plan`. | Ignored while the main session is in auto, acceptEdits or bypass mode (auto is the default on Pro, Max and Team). `bypassPermissions` here never escalates. |
| `mcpServers` | MCP servers only this agent gets: a configured server's name or an inline definition. | Inline servers keep their tools out of your main context. They connect when the agent starts and disconnect when it ends. |
| `hooks` | Hooks active only while the agent runs; Stop becomes SubagentStop. | Project agents: only after you trust the folder. Settings and plugin hooks already fire inside subagents. |
| `background` | `true` keeps it in the background even when Claude wants to wait. | Interactive sessions already run subagents in the background by default. |
| `isolation` | `worktree`: runs in a temporary git worktree, removed if nothing changed. | Branches from the **default branch**, not your HEAD, so it does not see uncommitted work. |
| `omitClaudeMd` | `true`: start without user, project and local CLAUDE.md (managed still loads). | For agents that get everything from the task. Needs v2.1.271 or later. |
| `experimental` | `cacheTtl: 5m` or `1h`: prompt-cache lifetime for this agent's requests. | Must be nested under `experimental`. `1h` is ignored on usage credits. |

> **Exam traps** `permissionMode` is ignored while the main session is in auto, acceptEdits or bypass mode. `isolation: worktree` branches from the default branch, not HEAD: wrong for reviewing uncommitted work, right for parallel edits. `memory` quietly adds Write and Edit. Plugin agents ignore `hooks`, `mcpServers` and `permissionMode`, and do not support `color` or `initialPrompt`. A subagent returns only its summary; its file reads never reach your context.

::: quiz Check yourself: level 7
- A subagent sets `permissionMode: plan`; the main session runs in auto. Which mode applies?
- What returns to the main context when a subagent finishes?
- Why is `isolation: worktree` wrong for reviewing uncommitted changes?
- Which two fields are required?
Answers:
- Auto.
- Only its summary.
- The worktree branches from the default branch, so uncommitted changes are not in it.
- `name` and `description`.
:::

<!-- eyebrow: Level 8 · Plugins -->
## One folder that packages everything, so it can be versioned and shared.

> **Big idea** A plugin is a folder that packages skills, agents, hooks, MCP and LSP servers and more, so they can be installed, versioned and shared as one unit. Only `.claude-plugin/plugin.json` has a fixed location, and even the manifest is optional: without it, components are found in their default folders and the plugin is named after the folder.

> **Java anchor** A Spring Boot starter published to Artifactory: one versioned artifact that auto-configures several components. The marketplace is your Maven repository, and `enabledPlugins` is your dependency list. Setting `version` is like releasing 1.0.0 instead of a SNAPSHOT: consumers only move when you publish a new version.

```flow
my-plugin/
├── .claude-plugin/
│   └── plugin.json          manifest: the only file in this folder
├── skills/<name>/SKILL.md   skills, invoked as /my-plugin:<name>
├── commands/*.md            single-file skills (older form)
├── agents/*.md              subagents, shown as my-plugin:<name>
├── workflows/*.js           dynamic workflow scripts
├── hooks/hooks.json         hooks, same format as the "hooks" key in settings.json
├── .mcp.json                MCP servers, started when the plugin is enabled
├── .lsp.json                language servers for code intelligence
├── monitors/monitors.json   background watchers (experimental)
├── output-styles/*.md       output styles
├── themes/*.json            color themes (experimental)
├── bin/                     executables added to the Bash tool's PATH
├── settings.json            defaults; only "agent" and "subagentStatusLine" are read
└── scripts/                 files your hooks and servers call (not auto-loaded)
```

### Five rules

1. **Keep `.claude-plugin/` for the manifest only.** Every other folder sits at the plugin root.
2. **A CLAUDE.md in a plugin is not loaded.** Ship instructions as a skill instead.
3. **Everything is prefixed with the plugin name**, so several plugins can each ship a `review` skill without clashing.
4. **Plugin agents ignore `hooks`, `mcpServers` and `permissionMode`** for security. Put hooks in `hooks/hooks.json`.
5. **Point at bundled files with `${CLAUDE_PLUGIN_ROOT}`.** Its path changes on every update, so keep lasting state in `${CLAUDE_PLUGIN_DATA}`. A plugin cannot reference files outside its own folder.

### plugin.json (from the review-kit plugin)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "review-kit",
  "displayName": "Review Kit",
  "version": "1.0.0",
  "description": "Code-review subagent, a review checklist skill, and a hook that blocks dangerous shell commands.",
  "author": { "name": "Janaka" },
  "license": "MIT",
  "keywords": ["code-review", "security", "hooks", "subagent"]
}
```

### Every manifest field

| Field | What it does |
|---|---|
| `name` | The only required field, in kebab-case. It becomes the prefix for every skill and agent. |
| `version` | A semantic version. Once set, users only get updates when you bump it. |
| `displayName`, `description` | What people see in the `/plugin` browser. `displayName` is never used for lookup. |
| `author`, `homepage`, `repository`, `license`, `keywords` | Optional metadata. |
| `$schema` | Editor autocomplete and validation. Ignored when loading. |
| `defaultEnabled` | `false` installs the plugin switched off until the user enables it. |
| `skills` | Extra skill folders, loaded on top of the default `skills/`. |
| `commands`, `agents`, `workflows`, `outputStyles` | Custom paths that **replace** the default folder. List the default too if you want to keep it. |
| `hooks`, `mcpServers`, `lspServers` | A path to a config file, or the config written inline. |
| `userConfig` | Values asked for when the plugin is enabled. `sensitive: true` stores them in secure storage instead of `settings.json`. |
| `dependencies` | Other plugins this one needs, optionally with version ranges like `~2.1.0`. |
| `experimental` | Paths for themes, monitors and evals, whose format may still change. |
| `channels` | Message channels (Slack- or Telegram-style) that push content into the session through the plugin's MCP server. |
| `metadata` | A free-form object for your own data. Claude Code ignores it. |

All paths in the manifest are relative to the plugin folder and start with `./`.

### The review-kit plugin, built and tested

Contents: `agents/code-reviewer.md` (the level 7 reviewer adapted for plugins: it lists `Skill` in its tools, its first step loads `review-kit:review-checklist`, and it drops `color` and `initialPrompt`), `skills/review-checklist/SKILL.md`, `hooks/hooks.json` plus `scripts/block-dangerous.sh`, and a README. Checked with Claude Code v2.1.278: `claude plugin validate --strict` passed, and `plugin details` found 1 skill, 1 agent and 1 PreToolUse hook, adding about 84 tokens to each session.

```bash
unzip review-kit.zip
claude plugin validate ./review-kit     # schema check
claude --plugin-dir ./review-kit        # load it for one session
cp -r review-kit ~/.claude/skills/      # load it in every project, from the next session
```

```json
{
  "description": "Deny catastrophic shell commands, ask before risky ones",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/block-dangerous.sh", "args": [], "timeout": 10 }
        ]
      }
    ]
  }
}
```

**Sharing.** Publish the plugin in a marketplace (a git repo with `.claude-plugin/marketplace.json`). Teammates add it with `/plugin marketplace add owner/repo` and install with project scope, which records it under `enabledPlugins` in the committed `.claude/settings.json`.

> **Exam traps** Only `plugin.json` goes inside `.claude-plugin/`. A plugin's CLAUDE.md is never loaded. With `version` set, new commits do not reach users until you bump it. If the same hook is in `settings.json` and in a plugin, both copies run.

::: quiz Check yourself: level 8
- Where does a plugin's hook configuration go?
- You pushed fixes, but users do not get them. Why?
- How do you try a plugin for one session without installing it?
- What does the `commands` field do to the default `commands/` folder?
Answers:
- `hooks/hooks.json` at the plugin root, or inline in `plugin.json`.
- `version` is set and was not bumped.
- `claude --plugin-dir ./my-plugin`.
- Replaces it, unless you list the default too.
:::

<!-- eyebrow: Level 9 · Commands -->
## The commands cheat sheet.

| Command | What it does |
|---|---|
| **Inside a session** | |
| `/init` | Generates a starter `./CLAUDE.md`; suggests improvements if one exists |
| `/memory` | Opens CLAUDE.md and auto memory; toggles auto memory |
| `/context` | Live context breakdown by category and tokens, including loaded memory files |
| `/status` | Shows the active settings sources, including managed |
| `/hooks` | Read-only browser of every hook and where it came from |
| `/config` | Change settings |
| `/plugin` | Browse, install and enable plugins and marketplaces |
| `/compact` | Summarises the conversation and reloads startup content |
| `/clear` | Starts fresh; picks up CLAUDE.md edits |
| `@"name (agent)"` | Forces a specific subagent |
| **In the terminal** | |
| `claude mcp add --scope project` | Adds an MCP server to `.mcp.json` (`--scope user` writes to `~/.claude.json`) |
| `claude plugin init <name>` | Scaffolds a plugin in `~/.claude/skills/<name>/` |
| `claude plugin validate <path> --strict` | Checks a plugin |
| `claude plugin details <name>` | Component inventory and token cost |
| `claude --plugin-dir <path>` | Loads a plugin for one session |
| `claude --agent <name>` | Runs a subagent definition as the whole session |
| `CLAUDE_CODE_NEW_INIT=1` | Interactive `/init` that can also set up skills and hooks |

<!-- eyebrow: Level 10 · Recap -->
## The whole page in five minutes.

> **Keep this** Two layers: Claude *reads* CLAUDE.md, rules, memory, skills and agent prompts; the harness *applies* settings, permissions and hooks. Plugins package; MCP connects. ALON: Always (CLAUDE.md, MEMORY.md), Listed (skill and agent descriptions, MCP names), On use (SKILL.md, path rules, schemas), Never (settings, hooks, subagent work). Scopes: Organization → User → Project → Local. Settings follow M-C-L-P-U. CLAUDE.md is additive. Skills: managed > user > project. Subagents: managed > CLI > project > user > plugin. Hooks merge. Requests: S → P → C. CLAUDE.md is a user message after the system prompt, read once at startup. Settings hot-reload; CLAUDE.md does not. `/compact`: startup content reloads, the skill listing does not, invoked skills do (capped). Hooks: 33 events; the core loop is SessionStart → UserPromptSubmit → [PreToolUse → PermissionRequest → PostToolUse]↻ → Stop → SessionEnd. Exit codes: 0 go, 2 no, anything else shrug; silence is not approval; timeouts and missing scripts fail open. Hard rule → `permissions.deny`; rule with logic → hook. Subagents: own context, summary back, launched via the Agent tool; `permissionMode` ignored in auto, acceptEdits and bypass; worktree branches from the default branch. Plugins: only `plugin.json` in `.claude-plugin/`, no CLAUDE.md, everything prefixed, `version` pins updates.

```flow
              guidance (Claude reads)              enforced (harness applies)
  ALWAYS      CLAUDE.md · rules · MEMORY.md         settings · permission rules · modes
  LISTED      skill + agent descriptions · MCP names
  ON USE      SKILL.md · path rules · nested CLAUDE.md · MCP schemas
  NEVER       a subagent's own work (summary only)   hooks (they run, they don't load)

  scopes      ORG ▶ USER ▶ PROJECT ▶ LOCAL          settings win order  M ▶ C ▶ L ▶ P ▶ U
  request     SYSTEM ▶ PROJECT CONTEXT ▶ CONVERSATION
  loop        SessionStart ▶ UserPromptSubmit ▶ [PreToolUse ▶ Permission ▶ PostToolUse]↻ ▶ Stop ▶ SessionEnd
  exit codes  0 go · 2 no · other shrug · silence ≠ yes
```

<!-- eyebrow: Level 11 · Practice -->
## Fifteen exam-style questions.

Four options, one best answer. Written from the docs as practice, not taken from the real exam. Tags: [D2] Claude Code Configuration and Workflows, [D5] Context Management and Reliability. Answer all fifteen before opening the answer key in the next section.

1. **[D2]** A bank's platform team must guarantee that no developer's Claude Code session can run `sudo`, whatever developers put in their own or project settings. What should they do? **A.** Add "Never use sudo" to the managed CLAUDE.md. **B.** Add a PreToolUse hook that blocks sudo to each repository's `.claude/settings.json`. **C.** Add a `Bash(sudo *)` deny rule to managed settings. **D.** Add `disallowedTools: Bash(sudo *)` to every subagent.
2. **[D5]** A developer adds a new rule to CLAUDE.md halfway through a session, but Claude keeps ignoring it. What is the most likely reason? **A.** CLAUDE.md is read once at session start; the edit loads after `/clear`, `/compact` or a restart. **B.** The rule must be moved into `.claude/CLAUDE.md` to be read. **C.** CLAUDE.md is only read by subagents. **D.** The rule needs a SessionStart hook to activate.
3. **[D5]** Your team has a 3,000-line migration runbook that Claude needs only when a migration task comes up. You do not want to pay its tokens in every session. What is the best option? **A.** Paste it into the project CLAUDE.md. **B.** Print it from a SessionStart hook. **C.** Put it into the output style. **D.** Package it as a skill with a clear description.
4. **[D5]** You need Claude to audit a large codebase for security issues without flooding the main conversation with hundreds of file reads. What is the best approach? **A.** Load a security-checklist skill in the main session. **B.** Delegate the audit to a subagent that returns a summary. **C.** Add a PostToolUse hook that scans each file Claude reads. **D.** Run `/compact` after every few file reads.
5. **[D2]** A PreToolUse policy hook meant to stop `rm -rf ~` writes an error to stderr and exits with code 1. Claude runs `rm -rf ~`. What happens? **A.** The command is blocked and Claude sees the stderr text. **B.** Claude Code asks the user for permission. **C.** The command runs, because exit 1 is a non-blocking error. **D.** The session ends.
6. **[D5]** After `/compact`, Claude stops picking up several skills it used to use automatically, although a skill it invoked earlier still works. Why? **A.** The skill listing is not re-injected after compaction; only invoked skill bodies are. **B.** Compaction disables all model-invocable skills until restart. **C.** After compaction, skills load only inside subagents. **D.** Compaction clears the skill folders' cache on disk.
7. **[D2]** `~/.claude/settings.json` sets the model to haiku, the project's `.claude/settings.json` sets opus, and `.claude/settings.local.json` sets sonnet. There are no CLI flags or managed settings. Which model is used? **A.** opus, because shared project settings keep the team consistent. **B.** haiku, because user settings follow you everywhere. **C.** Whichever file was saved most recently. **D.** sonnet, because local project settings override shared project settings.
8. **[D2]** A subagent's frontmatter sets `permissionMode: plan`, but the developer runs the main session in auto mode. How does the subagent run? **A.** In plan mode, as its frontmatter says. **B.** In auto mode, because the main session's mode wins when it is auto, acceptEdits or bypassPermissions. **C.** In default (Manual) mode. **D.** It refuses to launch because the modes conflict.
9. **[D2]** You give a subagent `isolation: worktree` so it can try refactors safely. It reports that it cannot find changes you made this morning and have not committed. Why? **A.** Worktrees are read-only. **B.** Worktree subagents cannot use Bash. **C.** The worktree branches from the default branch, not your current HEAD, so uncommitted work is not there. **D.** The worktree is deleted before the subagent starts.
10. **[D2]** Where should a plugin's hook configuration live? **A.** `hooks/hooks.json` at the plugin root, or inline in `plugin.json`. **B.** `.claude-plugin/hooks.json`. **C.** In the frontmatter of the plugin's agents. **D.** In a CLAUDE.md at the plugin root.
11. **[D2]** A skill named `deploy` exists in `~/.claude/skills/deploy/` and another in the repo's `.claude/skills/deploy/`. There is no managed skill. Which one does Claude use? **A.** The project one, because project configuration always beats personal configuration. **B.** Both, merged into one skill. **C.** Neither, because Claude Code refuses duplicate names. **D.** The personal one, because for skills user beats project.
12. **[D2]** Your plugin's `plugin.json` has `"version": "1.0.0"`. You push several fixes without changing it. What do users get? **A.** The fixes, automatically, on next startup. **B.** Nothing new: with a version set, users only get updates when you bump it. **C.** An error because the version is stale. **D.** A prompt asking whether to update.
13. **[D2]** A PreToolUse hook exits 0 with no output for a command. What does that mean? **A.** The command is approved and skips permission checks. **B.** The command is denied. **C.** The hook has no opinion; the normal permission flow decides. **D.** Claude is asked to retry the tool call.
14. **[D2]** Which of these is NOT a way to deliver organization-managed Claude Code settings? **A.** A `managed-settings.json` file in the system configuration folder. **B.** MDM or OS policy (macOS plist, Windows registry). **C.** Server-managed settings from the claude.ai admin console. **D.** A `"managed": true` flag inside `~/.claude/settings.json`.
15. **[D5]** Which of these belongs to the system-prompt layer of a Claude Code request, rather than the project-context layer? **A.** Tool definitions and the git status snapshot. **B.** `~/.claude/CLAUDE.md`. **C.** The first 200 lines of MEMORY.md. **D.** Unscoped rules in `.claude/rules/`.

Score: ____ / 15. For every miss, re-read the level named in the answer key.

<!-- eyebrow: Level 12 · Answer key -->
## Why each answer is right, and why each distractor is wrong.

::: fold Open the answer key only after answering all fifteen
1. **C** (level 2). Managed settings sit at the top of the precedence chain and cannot be overridden, and deny rules are enforced by the harness. A: CLAUDE.md is guidance. B: developers can edit project files, and a hook that times out or cannot start fails open. D: covers subagents only, and `Bash(sudo *)` in `disallowedTools` removes all of Bash.
2. **A** (level 3). CLAUDE.md is read once at startup and held in memory. B: `./CLAUDE.md` and `./.claude/CLAUDE.md` both work. C: the main session loads it. D: no hook is needed; the file just has not been re-read.
3. **D** (levels 1 and 6). Only the skill's name and description are listed; the body loads when the task matches. A: CLAUDE.md loads in full every session. B: SessionStart output is added at every start. C: the output style is part of every request's system prompt.
4. **B** (level 7). The subagent's reads stay in its own context; only the summary returns. A: a skill adds instructions to the current context, and the reads still land there. C: a hook runs a script per tool call; it does not move the work out of the main context. D: compaction loses detail and still processes every read first.
5. **C** (level 4). Only exit 2, or a JSON deny, blocks. A describes exit 2. B describes the JSON `permissionDecision` "ask". D: hooks do not end sessions like this.
6. **A** (level 3). The listing is the only startup content not re-injected; invoked skills are preserved (capped). B: skills are not disabled. C: invented behaviour. D: compaction does not touch files on disk.
7. **D** (level 2). Local > Project > User (M-C-L-P-U). A: project ranks below local. B: user is the lowest file scope. C: precedence is fixed, not time-based.
8. **B** (level 7). In auto, acceptEdits or bypass mode, the subagent runs in the main session's mode and its `permissionMode` is ignored. A: the field applies only when the main session is in default, dontAsk or plan. C: nothing resets to default. D: there is no conflict error.
9. **C** (level 7). A worktree branches from the default branch, not HEAD. A: worktrees are writable; that is their point. B: tools are set by `tools` and `disallowedTools`, not by isolation. D: a worktree is removed only after the run, and only if nothing changed.
10. **A** (level 8). B: `.claude-plugin/` may contain only `plugin.json`. C: plugin agents ignore `hooks`. D: a plugin's CLAUDE.md is not loaded.
11. **D** (level 2). Skills resolve managed > user > project. A: that is the subagent rule, a classic mix-up. B: skills do not merge. C: duplicates resolve by priority.
12. **B** (level 8). A set version pins the plugin; new commits under the same version are not delivered. A: would need a version bump. C and D: no such error or prompt exists.
13. **C** (level 4). Silence means no opinion. A: approval must be returned explicitly as JSON. B: denial needs exit 2 or a JSON deny. D: there is no retry mechanism.
14. **D** (level 2). There is no such flag, and user settings are the lowest file scope, editable by the user. A, B, C: all three are documented delivery channels.
15. **A** (level 3). Tool definitions are in the system prompt, and the git snapshot is its last block. B, C, D: all three are project context, sent as a message after the system prompt.
:::

### Sources

- [Explore the .claude directory](https://code.claude.com/docs/en/claude-directory): every file and where it lives
- [Extend Claude Code](https://code.claude.com/docs/en/features-overview): when to use each feature and how they layer
- [Settings](https://code.claude.com/docs/en/settings): scopes and precedence
- [Managed settings](https://code.claude.com/docs/en/managed-settings): organization policy
- [Memory](https://code.claude.com/docs/en/memory): CLAUDE.md, rules and auto memory
- [Explore the context window](https://code.claude.com/docs/en/context-window): what loads and when
- [Prompt caching](https://code.claude.com/docs/en/prompt-caching): the three request layers
- [Hooks reference](https://code.claude.com/docs/en/hooks): events, exit codes, JSON output
- [Subagents](https://code.claude.com/docs/en/sub-agents): definition files and fields
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference): layout and plugin.json
- On this site: [MCP end to end](/academy/modules/2026/FSE/mcp-end-to-end.html), the protocol behind the MCP box in the map.
