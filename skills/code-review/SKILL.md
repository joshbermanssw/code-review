---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) with a panel of specialist reviewers run as parallel sub-agents: Spec, Standards and Correctness always, plus Security (security), Architecture (architecture), Fallow (fallow static analysis) and Visual (the rendered UI) when the diff earns them, and up to 5 Ad Hoc reviewers for niche questions only when needed. Reports one recommendation: what to fix before merge and what to raise as comments. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
argument-hint: "<fixed point> [security|architecture|visual|skip security|skip architecture|skip visual|skip ad-hoc]"
---

## Runtime compatibility

Invoke as `$code-review` in Codex or `/code-review` in Claude Code. Slash-prefixed skill examples below use Claude Code syntax; in Codex, load the named skill with its arguments from the user message. Resolve bundled files relative to this `SKILL.md`, including when installed through a symlink.

Use the current host's available shell, file, question, skill-loading, and delegation tools. Claude tool names and model tiers below are examples, not portable API identifiers. In Codex, load a referenced skill by reading its `SKILL.md`; delegate with the native agent tool and inherit the session model unless the user or applicable instructions request a supported override. If delegation is unavailable, do ordinary steps in-session; report an independent review as unavailable rather than claiming you ran one. Pass these runtime rules to delegates.

Panel review of the diff between `HEAD` and a fixed point the user supplies. This skill is the **orchestrator**: it pins the diff, picks which specialists the diff earns, runs them as parallel sub-agents, verifies what they report, and presents one recommendation drawn from all of them.

**Hard rule: every reviewer you pick runs as its own sub-agent (Agent tool), whatever the diff's size.** Never review inline in place of a sub-agent, and never label your own read "ran inline". The user invoking this skill is the request for independent reviewers. The only legitimate skips are step 3's, each recorded with a reason. If the Agent tool is unavailable, say so and stop; don't substitute your own review.

Each specialist lives in `reviewers/<name>.md` with the same five parts: **Runs**, **Model**, **Hand it**, **Brief**, **Output**. To add a reviewer, add a file there and a row to the roster below. Severity and proof rules shared by every reviewer live in [rubric.md](rubric.md).

## Roster

| Reviewer | File | Runs |
|---|---|---|
| **Spec** | [reviewers/spec.md](reviewers/spec.md) | Always, unless there's no spec and no PR body |
| **Standards** | [reviewers/standards.md](reviewers/standards.md) | Always |
| **Correctness** | [reviewers/correctness.md](reviewers/correctness.md) | Always |
| **Security** | [reviewers/security.md](reviewers/security.md) | When the diff hits a security trigger |
| **Architecture** | [reviewers/architecture.md](reviewers/architecture.md) | When the diff hits an architecture trigger |
| **Fallow** | [reviewers/fallow.md](reviewers/fallow.md) | When the repo has a `package.json` and the diff touches JS/TS/CSS |
| **Visual** | [reviewers/visual.md](reviewers/visual.md) | When the diff changes anything on screen |
| **Ad Hoc** | [reviewers/ad-hoc.md](reviewers/ad-hoc.md) | Up to 5, only when the diff raises a specific question no reviewer above covers |

The orchestrator itself also runs the **cheap checks** in step 4. They need no agent.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside parallel sub-agents.

Read the diff yourself. Triage in step 3 depends on it.

### 2. Gather the spec and PR body

Look for the originating spec, in this order:

1. Issue references in the commit messages or PR body (`#123`, `Closes #45`, etc.), fetched with `gh issue view <n> --json title,body,comments` (or the repo's tracker, if it documents another).
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, or a caller (such as `/pr`) said the issue is "none", don't ask: Spec reviews against the PR body alone, or is skipped with "no spec available" when there's no body either.

If a PR exists for the branch, read its body: `gh pr view --json number,title,body,url`. Spec checks it against the diff. Before the PR exists (first `/pr` run) there's no body, and Spec's body check is skipped.

### 3. Triage the reviewers

Spec, Standards and Correctness always run. For Security, Architecture, Fallow and Visual, read each one's **Runs** triggers and check them against the diff. Any one trigger is enough.

Then decide whether the diff needs any **Ad Hoc** reviewers: up to 5, each written from the template in [reviewers/ad-hoc.md](reviewers/ad-hoc.md), and only when you feel one is necessary. Needing none is the normal result, and it needs no skip reason.

**Skip Security and Architecture** when the diff is only docs, copy, comments, formatting, a lockfile bump, test-only changes, or a config value with no security or structural surface. A new runtime dependency still triggers Security, even when it arrives through a lockfile. **Skip Visual** only when nothing changes on screen.

**The user's word beats the triggers, in both directions.** `security`, `architecture` or `visual` in the arguments (or "run Security on this") forces a reviewer on; `skip security`, `skip architecture`, `skip visual` or `skip ad-hoc` turns one off. Mid-review is fine: if something trips a trigger you had ruled out, spawn that reviewer then and say you did.

Record each skipped reviewer with a one-line reason. A silently skipped reviewer reads as a clean one, and that is the failure triage must not cause.

### 4. Cheap checks

Run these yourself before spawning the reviewers. Each finding goes in the report like any other.

- **Changeset.** If the repo has `.changeset/config.json` and the diff changes what a published package ships, there must be a new `.changeset/*.md`. A missing one is always a **Major**, even though nothing visibly breaks: the fix either never reaches npm or rides out undocumented in someone else's release. A PR that ships nothing from a package (tests, CI, docs outside a package), or carries the repo's skip label (`skip-changeset` on tinacms), needs none.

### 5. Spawn the chosen reviewers in parallel

Issue every chosen reviewer's sub-agent call together, in a single message, in the foreground. A small diff is not a reason to do any of this yourself. For each one:

- Use the model its file names, and the effort too when it names one.
- Paste in its **Brief**, its **Output** contract, the shared [rubric.md](rubric.md), and everything its **Hand it** list asks for. The sub-agent has no other access to these.
- Always include the diff command, the commit list, and one line on anything you already suspect, so it doesn't spend its budget rediscovering it.

### 6. Verify

Reviewer findings are hypotheses, not facts. Before reporting:

- Every finding tagged **inferred** becomes a **Question**, unless you do the reading yourself and can cite the `file:line` that proves it.
- Gather every **Critical** and **Major** that survives, from every reviewer, and hand the full finding records (including each one's **detail**) to **one fresh `opus` sub-agent** with the diff, briefed to try to disprove each one against the source, any screenshot named in its detail and the proof rules in [rubric.md](rubric.md), and to return **keep**, **downgrade to <severity>** or **drop** per finding with a one-line reason. For each one it keeps, it also returns where to solve it, with a one-line reason: **this PR** when the diff caused or worsened it, or the PR's PBI or spec requires it; **another PBI** when it was already there and fixing it isn't needed for this PR's goal. When unsure, it's **this PR**. That says which PR the fix belongs in, not whether it blocks the merge. The agent that checks a finding is never the one that found it. Apply its verdicts and note each change in that finding.
- Drop any finding with no anchor (the rubric's evidence-or-drop rule). A Spec finding about something missing from the diff is anchored by the spec quote it cites.

### 7. Report

If Security found a leaked credential, lead the report with it (see [reviewers/security.md](reviewers/security.md)).

Then the report, and nothing else: no per-reviewer sections, status lines, tallies or `## Checks`. It is the whole output, so every surviving finding that belongs in it must appear in full.

```markdown
**<Approve | Approve with comments | Request changes>:** <the reason, in plain words>

**Before Merge:**
- [Major] ...
- [Minor] ...

**Raise as Comments:**
- [Question] ...

**Solve in Another PBI:**
- [Critical] ... <why it isn't this PR's to fix>

**Coverage:** <reviewers that came back clean and what they checked, including each Ad Hoc question and its answer; each skipped reviewer with its reason; Security's Hardening notes, if any>
```

- **Before Merge** holds what must change, most severe first; **Raise as Comments** holds what's worth asking the author about without blocking. **Solve in Another PBI** holds the Critical and Major findings the verifier placed in another PBI; they don't block this PR, and the closing offer includes raising them as PBIs. Leave out a heading with nothing under it.
- **Omit from the output:** all nits, and every Minor that isn't under Before Merge. A Minor belongs under Before Merge only when it's worth holding the merge for, so never list one anywhere else. A finding downgraded to Minor in step 6 follows this rule, whatever the verifier said about where to solve it: under Before Merge only when it's worth holding the merge for, otherwise omitted.
- Write each finding so the reader understands it without opening the code (see "Writing a finding" below). Never report one as an anchor plus a fragment.
- Findings that two reviewers raised about the same thing appear once.
- Close by offering the next action, such as posting the review with that verdict.

### Posting to the PR

Only post when the user asks. **Strictly inline comments and suggestions, never a body comment:** post the findings the user picked as one review (`gh api repos/{owner}/{repo}/pulls/<n>/reviews` with a `comments` array) and leave its `body` empty. Don't use `gh pr comment`, and don't paste the report into the PR.

- Anchor each finding on its `file:line`, one comment per finding, written in the "Writing a finding" shape.
- When the fix is a concrete line change, write it as a GitHub ```` ```suggestion ```` block so the author can apply it.
- A finding with no line in the diff (such as something missing) goes on the closest changed line. If there is none, don't post it: tell the user in the chat.
- If GitHub refuses the review without a body, stop and tell the user rather than adding one.

### Writing a finding

Each finding is one bullet: its severity in square brackets, a bold title that names the problem in plain words, then two to four plain sentences:

1. **What goes wrong**, from the user's or reader's point of view.
2. **A concrete example**: the input or config, and what happens.
3. **Why it matters**: what breaks, drifts or misleads someone later.
4. **Fix:** the smallest change, starting with the bold word.

Put the anchor (`file:line`) in the sentences or after the title, never as the title. Define any term a reader might not know.

Example:

```markdown
- [Minor] **The two reference walks disagree on a single string in a reference list.** Take `related: t.array({ of: t.reference(...) })` where the file has `related: content/posts/a.md`, a single string instead of a list. `collectReferences` (`core/form/references.ts:54`) wraps it and reports it as a reference, so the preview fetches that document, but `resolveReferences` only handles real lists and never swaps it in. That is a wasted fetch, and two walks that disagree about the same value. **Fix:** only walk items when the value is actually a list for `of` fields.
```

When reporting back after acting on findings, use the same shape per finding: a bold heading for the problem, one or two sentences on what was wrong, then what you changed, or why you left it (and what would change that).

### 8. Record the run

After the report, pipe one record to [ledger/record.py](ledger/record.py) so the run shows up on the dashboard. Don't print the record, and only mention this step if it fails. A failed record never changes the review. Numbers and short labels only: the script rejects any other field, so never try to fit finding text or code in.

```json
{
  "repo": "owner/name", "pr": 123, "sha": "<reviewed HEAD>",
  "caller": "manual | pr | automation",
  "verdict": "approve | approve-with-comments | request-changes",
  "reviewers": [
    {"name": "Visual", "status": "ran", "model": "opus", "tokens": 41000, "seconds": 190,
     "raised": {"major": 2, "minor": 1}, "kept": {"major": 1}, "another_pbi": 0, "omitted": 1, "dropped": 1},
    {"name": "Security", "status": "skipped"},
    {"name": "Ad Hoc", "status": "ran", "topic": "webhook-retries", "model": "sonnet", "raised": {}, "kept": {}}
  ]
}
```

- **One entry per reviewer**, including skipped ones and each Ad Hoc. `pr` is left out when there's no PR. `tokens` and `seconds` come from the sub-agent's result; leave them out if it doesn't give them.
- **`raised`** counts by severity before verification. **`kept`** counts what the report shows, by final severity. **`another_pbi`**, **`omitted`** (Minors and nits left out) and **`dropped`** (overturned or unanchored) count the rest.
- **`topic`** is a short slug that names the kind of check, never the question itself, because a question can reveal private details.

### Ledger and dashboard

Records go in `$CODE_REVIEW_LEDGER`, or `~/.code-review-ledger` if that isn't set. To store them somewhere else, set that variable in your shell profile. Each saved record rebuilds the dashboard, `reviews.html`, in that folder. To rebuild it yourself, run [ledger/dashboard.py](ledger/dashboard.py), which needs only Python 3 and can write elsewhere with `--out <file>`.

## Re-running after fixes

Guidance for callers such as `/pr`. Each run is fresh and can't tell it's a re-run, so the caller applies these rules through `skip security` / `skip architecture` / `skip visual` / `skip ad-hoc` args:

- **Spec, Standards and Correctness** always re-run.
- **Security** re-runs when the fix touched the security surface (the check that was added, the query predicate, the header, the policy). A two-line correction is exactly where a new hole gets introduced.
- **Architecture** re-runs only when the fix reshaped the change. A shape that was sound before a small correction is still sound.
- **Fallow** always re-runs when it ran before. It's cheap and deterministic.
- **Visual** re-runs after any fix that changes what renders, pointed at the surfaces its findings named and whatever shares their space.
- **Ad Hoc** re-runs only for a reviewer that had a finding, to check that fix. Triage may still write new ones if the fix raises a new question.

## Why one report

Reviewers still run separately, so a change can pass one and fail another: code that follows every standard can still implement the wrong thing. That separation matters during the review. The reader needs one decision at the end.
