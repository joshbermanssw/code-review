# Code Review

Reviews a diff with a panel of specialist sub-agents, then gives you one recommendation: what to fix before merge, and what to raise as comments.

Spec, Standards and Correctness always run. Security, architecture, static analysis and visual reviewers join when the diff earns them. The main agent can also write up to 5 ad hoc reviewers for questions specific to your change. A separate agent then tries to disprove every Critical and Major finding before you see it.

## Install

In Claude Code:

```
/plugin marketplace add joshbermanssw/code-review
/plugin install code-review@code-review
```

Then run `/code-review:code-review <base branch>`.

For other agents, use `npx skills add joshbermanssw/code-review`.

## Requirements

- `git`, Python 3 and Node
- `gh`, for reading and commenting on GitHub PRs

Some reviewers download and run third-party tools through `npx`: the static analysis reviewer runs [fallow](https://github.com/fallow-rs/fallow), and the visual reviewer runs [Playwright](https://playwright.dev) and starts your app on a spare port. To turn them off for a run, pass `skip visual`, or remove `reviewers/fallow.md` and its roster row.

## The report

```
Request changes: phone users can't delete files with long names.

Before Merge:
- [Major] The Delete button can't be reached on a phone. ...

Raise as Comments:
- [Question] Should links expire? ...

Coverage: Spec and Correctness came back clean. Security was skipped: the diff is UI only.
```

It leaves out nits, and any Minor that isn't worth holding the merge for. Nothing goes on a PR unless you ask, and then only as inline comments and suggestions.

## Ledger and dashboard

Each review saves a small JSON record: reviewer names, counts, tokens and time, never finding text or code. Records stay on your machine, in `~/.code-review-ledger`. To keep them somewhere else, set `CODE_REVIEW_LEDGER`.

To see which reviewers find real problems and what they cost, open `reviews.html` in the ledger folder. It rebuilds after every review.

## Licence

MIT. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the work this builds on.
