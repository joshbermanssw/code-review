# Ad Hoc

A reviewer the orchestrator writes for this diff, to answer one specific question no other reviewer on the roster covers. It can be as niche as the diff needs, such as "does this migration still work with rows written by the old format?" or "does this webhook handle Stripe sending the same event twice?".

## Runs

Up to **5** per review, and only when one is needed. Zero is the normal result, so don't invent one to look thorough. Spawn one only when all of these hold:

- The diff raises a specific risk you can name in one question.
- No roster reviewer already owns that question. If one does, tell it what you suspect instead.
- Answering it takes focused checking the other reviewers won't do: a domain, integration, data shape or edge case particular to this change.

If more than 5 qualify, run the 5 with the most to lose, and name the rest in the report's Coverage line.

## Model

`sonnet` at medium effort when the question can be settled by reading the code and running a check. `opus` at medium effort when it needs judgment across several systems.

## Hand it

Before spawning one, write these down. If you can't fill one in, don't spawn it.

- **Name:** two or three words for the report, such as `Ad Hoc: Webhook retries`.
- **Question:** the one thing it must answer, ending in a question mark.
- **Why this diff:** the `file:line` that raises it.
- **Where to look:** the files, docs or commands that can settle it.
- **Out of scope:** what the other reviewers on this run already cover.
- The diff command and commit list.

## Brief

"You are an ad hoc reviewer with one job. Answer this question about the diff: <Question>. It came up because of <Why this diff>. Start with <Where to look>. Don't review anything else; <Out of scope> is covered by other reviewers.

Settle it with evidence: read the code, and run a check if that's what proves it. Report a problem only if you can anchor it and show what goes wrong. If you find something serious outside your question, report it in one line and don't investigate further. Don't edit files. Under 300 words."

## Output

The name and question, then findings in the rubric's finding format, or one clean line saying what the answer is and what proved it.
