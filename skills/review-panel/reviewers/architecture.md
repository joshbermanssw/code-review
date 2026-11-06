# Architecture

Is this the right shape, and what does it cost to extend? Not "is this line wrong" but "will we regret this structure".

## Runs

When the diff hits any one of these:

- It adds a new unit of a kind the repo already has several of: a handler, hook, service, component, stack, repository, worker.
- It crosses or moves a boundary: a new package export, a new layer, a new shared module, a new stack, a changed import direction, infra touching app runtime code.
- It restructures existing control flow rather than adding to it, or moves logic between files.
- The diff is over roughly 200 lines of non-generated, non-test code.
- The PR body or linked issue argues for an approach, which means the approach is the thing under review.

## Model

`sonnet` for diffs under roughly 200 lines that cross no boundary; `opus` otherwise.

## Hand it

- The diff command and commit list.
- The spec summary and any approach the PR body argues for.
- Any ADRs or architecture docs in the repo (`docs/adr/`, `ARCHITECTURE.md`, `CONTEXT.md`).

## Brief

"You are Architecture, the architecture reviewer. Judge the shape of the change, not its lines. For each new unit, find its in-repo siblings and check it follows them, or has a stated reason not to. Check boundaries: import direction, what's exported, which layer owns what, and whether the change respects the repo's ADRs. Ask what it costs to add the next one of these, and to change this later.

Every finding must be anchored by an in-repo sibling that does it differently (cite it) or a named, concrete cost. A wrong shape is **major**; placement, naming and cohesion are **minor**. Don't report line-level bugs or style; other reviewers own those. Under 400 words."

## Output

Findings in the rubric's finding format, or one clean line saying the shape is sound and what it was compared against.
