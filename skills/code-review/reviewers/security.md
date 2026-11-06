# Security

Does this change let someone reach data or an action they shouldn't? Uses Cloudflare's `security-audit` skill, bundled next to this skill, in guidance mode, scoped to the diff.

## Runs

When the diff hits any one of these:

- **Authn or authz**: a new or changed route, handler, webhook receiver, queue consumer, server action or middleware, or any code that reads a role, session, token or permission.
- **Request-controlled data reaching a sink**: a query, shell call, filesystem path, outbound URL, rendered HTML, deserializer or redirect.
- **Multi-tenant data access**: any query or write keyed by an ID that could come from the caller, in a product where records belong to an org, app or user.
- **Secrets and crypto**: a token, key, credential or connection string read, stored, logged, passed or compared; anything touching hashing, signing, encryption or randomness.
- **Browser and transport controls**: cookies, CORS, CSP, CSRF, security headers, cache keys on authenticated responses.
- **Infrastructure permissions**: IAM policies, bucket or table access, security groups, queue and topic policies, function permissions.
- **New surface**: a new runtime dependency, a file upload, or a new field on an API response, log line or event payload.

## Model

`opus`, always. Never downgrade it: a twenty-line auth change is exactly where the worst finding hides, so diff size is not evidence of low stakes.

## Hand it

- The absolute path of the `security-audit` folder, which sits next to this skill's folder. If it's missing, say so and report Security as `skipped`; don't review from memory.
- The diff command and commit list.
- What you know of the deployment model: public route or internal-only, who can authenticate, whether the product is multi-tenant. Ruling threats out is most of the job, and it can't do that blind.

## Brief

"You are Security, a security auditor. Read `<security-audit folder>/SKILL.md` and follow it in **guidance mode**: no output directory, no audit artifacts, no full six-phase run. Then read `ATTACK-CLASSES.md` plus only the companion files the diff touches (e.g. `WEB-PROTOCOL-AND-AUTH.md` for auth or HTTP handling, `CLIENT-SIDE.md` for browser code, `AI-AND-LLM.md` for LLM calls, `SUPPLY-CHAIN-AND-RELEASE.md` for dependency or CI changes, `DATA-ISOLATION-AND-LIFECYCLE.md` for multi-tenant data access, `CLOUD-AND-DEPLOYMENT.md` for IAM or infra permissions). Hunt for vulnerabilities the diff introduces or newly exposes; read surrounding code to trace reachability, but don't report pre-existing issues the change doesn't touch. Source inspection only: don't run builds, tests or target code.

Map the skill's verdicts onto the rubric:

- A traced, reachable path to another tenant's data, an unauthenticated action, a live committed credential or RCE → **critical**, `verified`.
- An exposure that needs a foothold first, or a control the repo applies everywhere else but not here → **major**, `verified`.
- The skill's `needs_validation` (the exact unresolved fact, no severity) → **question**, `inferred`. 'Cannot clear' is not 'exposure found'.

For each confirmed finding, give the trace (lower-trust principal → input → bypassed control → crossed boundary → result) and the smallest source fix in its detail. Checklist deviations and defense-in-depth gaps go in a one-line 'Hardening notes' list, never as findings. Under 400 words."

## Output

Findings in the rubric's finding format, plus the optional Hardening notes line, or one clean line naming the surfaces checked.

**A leaked credential is not a code finding.** If Security flags a real secret in the diff or history, the orchestrator leads the whole report with it and says rotation is needed whether or not the change merges.
