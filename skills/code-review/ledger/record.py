#!/usr/bin/env python3
"""Saves one code-review run to the ledger as a JSON file.

Usage: record.py < run.json
Exit 0: saved, prints the path, and rebuilds the dashboard. Exit 1: rejected, prints why, saves nothing.

Records hold numbers and short labels only. Any field not listed here is rejected, and
strings must match a short pattern, so finding text, code or secrets can't get in.

The ledger folder is $CODE_REVIEW_LEDGER, or ~/.code-review-ledger if that isn't set.
It lives outside the skill so updating the skill can't overwrite it.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SEVERITIES = {"critical", "major", "minor", "question"}
VERDICTS = {"approve", "approve-with-comments", "request-changes"}
CALLERS = {"manual", "pr", "automation"}
STATUSES = {"ran", "skipped", "failed"}

REPO = re.compile(r"[\w.-]{1,60}(/[\w.-]{1,60})?")
SHA = re.compile(r"[0-9a-f]{7,40}")
NAME = re.compile(r"[A-Za-z][A-Za-z -]{0,39}")
TOPIC = re.compile(r"[a-z0-9]+(-[a-z0-9]+){0,5}")
MODEL = re.compile(r"[a-z0-9][a-z0-9.-]{0,39}")


def ledger_dir():
    return Path(os.environ.get("CODE_REVIEW_LEDGER") or Path.home() / ".code-review-ledger")


def is_count(value):
    # bool is an int in Python, so rule it out by name.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def check_fields(item, allowed, where, errors):
    for key in item:
        if key not in allowed:
            errors.append(f"{where}: field not allowed: {key}")


def check_severity_counts(value, where, errors):
    if not isinstance(value, dict):
        errors.append(f"{where}: must be an object of severity counts")
        return
    for key, count in value.items():
        if key not in SEVERITIES or not is_count(count):
            errors.append(f"{where}: bad entry {key!r}")


def check_reviewer(item, where, errors):
    if not isinstance(item, dict):
        errors.append(f"{where}: must be an object")
        return
    allowed = {"name", "status", "topic", "model", "tokens", "seconds",
               "raised", "kept", "another_pbi", "omitted", "dropped"}
    check_fields(item, allowed, where, errors)
    if not (isinstance(item.get("name"), str) and NAME.fullmatch(item["name"])):
        errors.append(f"{where}: name must be a short reviewer name")
    if item.get("status") not in STATUSES:
        errors.append(f"{where}: status must be one of {sorted(STATUSES)}")
    if "topic" in item:
        if item.get("name") != "Ad Hoc":
            errors.append(f"{where}: only Ad Hoc reviewers have a topic")
        if not (isinstance(item["topic"], str) and TOPIC.fullmatch(item["topic"])):
            errors.append(f"{where}: topic must be a short-kebab-slug")
    if "model" in item and not (isinstance(item["model"], str) and MODEL.fullmatch(item["model"])):
        errors.append(f"{where}: bad model")
    for key in ("raised", "kept"):
        if key in item:
            check_severity_counts(item[key], f"{where}.{key}", errors)
    for key in ("tokens", "seconds", "another_pbi", "omitted", "dropped"):
        if key in item and not is_count(item[key]):
            errors.append(f"{where}: {key} must be a whole number")


def validate(run):
    if not isinstance(run, dict):
        return ["the record must be a JSON object"]
    errors = []
    check_fields(run, {"repo", "pr", "sha", "caller", "verdict", "reviewers"}, "run", errors)
    if not (isinstance(run.get("repo"), str) and REPO.fullmatch(run["repo"])):
        errors.append("run: repo must look like owner/name")
    if "pr" in run and not is_count(run["pr"]):
        errors.append("run: pr must be a number")
    if not (isinstance(run.get("sha"), str) and SHA.fullmatch(run["sha"])):
        errors.append("run: sha must be a commit hash")
    if run.get("caller") not in CALLERS:
        errors.append(f"run: caller must be one of {sorted(CALLERS)}")
    if run.get("verdict") not in VERDICTS:
        errors.append(f"run: verdict must be one of {sorted(VERDICTS)}")
    reviewers = run.get("reviewers")
    if not (isinstance(reviewers, list) and reviewers):
        errors.append("run: reviewers must be a non-empty list")
    else:
        for i, item in enumerate(reviewers):
            check_reviewer(item, f"reviewers[{i}]", errors)
    return errors


def main():
    try:
        run = json.load(sys.stdin)
    except ValueError as err:
        print(f"rejected: not valid JSON: {err}")
        return 1
    errors = validate(run)
    if errors:
        print("rejected:")
        for error in errors:
            print(f"- {error}")
        return 1
    now = datetime.now().astimezone()
    run["at"] = now.isoformat(timespec="seconds")
    folder = ledger_dir()
    folder.mkdir(parents=True, exist_ok=True)
    repo = run["repo"].replace("/", "-")
    target = run.get("pr") or run["sha"][:7]
    path = folder / f"{now:%Y-%m-%d-%H%M%S}-{repo}-{target}.json"
    path.write_text(json.dumps(run, indent=2) + "\n")
    print(path)
    # The record is what matters: a failed rebuild only warns.
    try:
        sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
        from dashboard import build
        build()
    except Exception as err:
        print(f"saved, but the dashboard didn't rebuild: {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
