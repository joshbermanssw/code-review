# Shared rubric

Every reviewer uses this scale and these proof rules. The orchestrator pastes this file into each reviewer's prompt.

## Severity

- **Critical**: data loss, a security hole, or the documented happy path breaks. Blocks merge.
- **Major**: wrong architecture, a real production failure mode with a verifiable code path, a regression this change introduces, or UI or UX that breaks at a width or state people will meet. Blocks merge.
  - UI or UX that breaks means a user can't see, reach or complete something: overlap, cut-off content, an unreachable control, a wrong state, or a flow that stops working.
  - "Failure" means something stops working, gives a wrong result, or loses data. Something that keeps working but is annoying, noisy, slower or uglier is not a failure, however many users it touches: that's Minor.
  - "Regression" means behaviour that worked before now doesn't. Replacing nothing with something imperfect is a trade, not a regression: Minor.
- **Minor**: code quality, docs, edge cases and defensive gaps with low real-world impact, and every annoyance-class finding (UX friction, accessibility chatter, perf that's worse but not broken). A Minor can still be worth fixing before merge; say so rather than inflating it.
- **Question**: an uncertain claim, or a Major-shaped concern that hasn't passed the proof rules below. The default for anything resting on an inferred assumption.

## Proof rules

Run these before calling anything Critical or Major. If one load-bearing assumption is still inferred rather than cited by `file:line`, it's a **Question**.

- **"X runs on Y"** → cite the wiring line (the route registration, event source, IaC stanza or handler map) that connects them. A filename that rhymes is not evidence.
- **"This races"** → cite the concurrency mechanism that allows it (standard vs FIFO queue, missing lock, parallel callers). A missing guard only matters if concurrent access is actually possible.
- **Live-symptom claims** → trace forward from the line that throws, not backwards from a theory.
- **User-impact claims** (accessibility, UX, performance) → name the observed behaviour or a standard the code demonstrably breaks. A code path alone is at most a Minor.

## Evidence or drop

Every finding needs an anchor: a `file:line`, a traced path, an in-repo precedent it breaks, or a named cost. Textbook findings with none ("violates SRP", "consider a factory", "unvalidated input", "add rate limiting") get dropped, not passed on. That noise is how a reviewer stops being believed.

## Finding format

Each finding carries:

- **severity**: critical / major / minor / question
- **confidence**: `verified` (you read the code that proves it and can cite it) or `inferred` (pattern, assumption, or unfinished trace)
- **anchor**: `file:line` or `file:start-end`. A Spec finding about something missing from the diff anchors on the spec or PR-body line it quotes instead.
- **title**: a few plain words naming the problem, e.g. "One bad item locks the whole blocks list".
- **explanation**: two to four plain sentences: what goes wrong from the user's or reader's point of view, a concrete example (input → result), and why it matters. Define any term a reader might not know.
- **fix**: the smallest change, in one sentence.
- **detail**: the trace behind it, for the verifier. The orchestrator uses it to check the finding, not as the explanation.

A clean result is a result: when there are no findings, say what you checked in one line.
