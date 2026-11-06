#!/usr/bin/env python3
"""Builds the code-review dashboard from the ledger, as one self-contained HTML file.

Usage: dashboard.py [--out <file>]
Prints the path it wrote. The default is reviews.html in the ledger folder.
"""
import json
import sys
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
from record import ledger_dir  # noqa: E402

RECENT = 25
CSS = """
:root { --bg:#f5f5f7; --panel:#fff; --ink:#1d1d1f; --muted:#6e6e73; --line:#e3e3e8;
        --kept:#2a78d6; --pbi:#c2610c; --dropped:#8a5cc2; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#111113; --panel:#1c1c1f; --ink:#f5f5f7; --muted:#a1a1a6; --line:#323236;
          --kept:#3f8ae0; --pbi:#d5752a; --dropped:#8f6bcb; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
main { max-width:1240px; margin:0 auto; padding:40px 16px 64px; }
h1 { font-size:32px; letter-spacing:-.02em; margin:0 0 4px; }
h2 { font-size:19px; margin:36px 0 10px; }
.sub, .note { color:var(--muted); }
.note { font-size:13px; margin:8px 0 0; }
.stats { display:flex; flex-wrap:wrap; gap:32px; margin:24px 0 0; }
.stats b { display:block; font-size:28px; letter-spacing:-.02em; font-variant-numeric:tabular-nums; }
.stats span { color:var(--muted); font-size:13px; }
.panel { background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow-x:auto; }
table { border-collapse:collapse; width:100%; min-width:760px; font-size:13.5px; }
th { color:var(--muted); font-weight:500; font-size:12px; text-align:right; vertical-align:bottom; }
th, td { padding:10px 10px; border-bottom:1px solid var(--line); }
tr:last-child td { border-bottom:0; }
td { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
th:first-child, td:first-child, .left { text-align:left; }
.repo { max-width:300px; overflow:hidden; text-overflow:ellipsis; }
.bar { display:flex; gap:2px; width:96px; height:10px; }
.bar i { display:block; height:100%; border-radius:3px; min-width:3px; }
.kept { background:var(--kept); } .pbi { background:var(--pbi); } .dropped { background:var(--dropped); }
.legend { display:flex; flex-wrap:wrap; gap:16px; font-size:13px; color:var(--muted); margin:10px 0 0; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; }
.empty { padding:48px 24px; text-align:center; color:var(--muted); }
"""


def load_runs(folder):
    runs = []
    for path in sorted(folder.glob("*.json")):
        try:
            run = json.loads(path.read_text())
        except ValueError:
            continue
        if isinstance(run, dict) and isinstance(run.get("reviewers"), list):
            runs.append(run)
    return sorted(runs, key=lambda r: r.get("at", ""), reverse=True)


def total(counts):
    return sum((counts or {}).values())


def summarise(runs):
    """Adds up each reviewer across runs. Ad Hoc reviewers are grouped under one name."""
    rows = defaultdict(lambda: defaultdict(int))
    for run in runs:
        for item in run["reviewers"]:
            row = rows[item.get("name", "?")]
            if item.get("status") != "ran":
                row["skipped" if item.get("status") == "skipped" else "failed"] += 1
                continue
            row["runs"] += 1
            kept = item.get("kept") or {}
            row["blocking"] += kept.get("critical", 0) + kept.get("major", 0)
            row["kept"] += total(kept)
            row["pbi"] += item.get("another_pbi", 0)
            row["omitted"] += item.get("omitted", 0)
            # Only records that say what was dropped count toward "Held up".
            if "dropped" in item:
                row["dropped"] += item["dropped"]
                row["verified"] += total(kept) + item.get("another_pbi", 0) + item.get("omitted", 0) + item["dropped"]
            if item.get("tokens") is not None:
                row["tokens"] += item["tokens"]
                row["costed"] += 1
            if item.get("seconds") is not None:
                row["seconds"] += item["seconds"]
                row["timed"] += 1
    return rows


def compact(number):
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    return f"{number / 1000:.0f}k" if number >= 1000 else str(number)


def bar(row):
    parts = [("kept", row["kept"], "reported"), ("pbi", row["pbi"], "another PBI"),
             ("dropped", row["dropped"], "dropped")]
    size = sum(count for _, count, _ in parts)
    if not size:
        return ""
    marks = "".join(
        f'<i class="{cls}" style="flex:{count}" title="{count} {label}"></i>'
        for cls, count, label in parts if count)
    return f'<div class="bar">{marks}</div>'


def reviewer_row(name, row):
    found = row["kept"] + row["pbi"] + row["omitted"]
    held = f"{1 - row['dropped'] / row['verified']:.0%}" if row["verified"] else "–"
    avg_tokens = compact(row["tokens"] // row["costed"]) if row["costed"] else "–"
    avg_time = f"{row['seconds'] / row['timed'] / 60:.1f}m" if row["timed"] else "–"
    per_finding = compact(row["tokens"] // found) if row["costed"] and found else "–"
    cells = [row["runs"], row["skipped"], row["blocking"], row["kept"], row["pbi"],
             row["omitted"], row["dropped"], held, avg_tokens, avg_time, per_finding]
    tds = "".join(f"<td>{cell}</td>" for cell in cells)
    return f'<tr><td>{escape(name)}</td>{tds}<td class="left">{bar(row)}</td></tr>'


def run_row(run):
    when = escape(str(run.get("at", ""))[:16].replace("T", " "))
    target = f"#{run['pr']}" if run.get("pr") else str(run.get("sha", ""))[:7]
    ran = [r for r in run["reviewers"] if r.get("status") == "ran"]
    kept = sum(total(r.get("kept")) for r in ran)
    pbi = sum(r.get("another_pbi", 0) for r in ran)
    dropped = sum(r.get("dropped", 0) for r in ran)
    tokens = sum(r.get("tokens") or 0 for r in ran)
    cells = (f'<td>{when}</td><td class="left repo" title="{escape(str(run.get("repo", "")))} {escape(target)}">{escape(str(run.get("repo", "")))} {escape(target)}</td>'
             f'<td class="left">{escape(str(run.get("caller", "")))}</td>'
             f'<td class="left">{escape(str(run.get("verdict", "")).replace("-", " "))}</td>'
             f"<td>{len(ran)}</td><td>{kept}</td><td>{pbi}</td><td>{dropped}</td>"
             f"<td>{compact(tokens) if tokens else '–'}</td>")
    return f"<tr>{cells}</tr>"


def ad_hoc_topics(runs):
    topics = defaultdict(lambda: [0, 0])
    for run in runs:
        for item in run["reviewers"]:
            if item.get("name") == "Ad Hoc" and item.get("status") == "ran":
                entry = topics[item.get("topic", "untitled")]
                entry[0] += 1
                entry[1] += total(item.get("kept")) + item.get("another_pbi", 0)
    return sorted(topics.items(), key=lambda kv: (-kv[1][0], kv[0]))


def render(runs, folder):
    built = datetime.now().strftime("%d %b %Y, %H:%M")
    head = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>Code Review Ledger</title><style>{CSS}</style></head><body><main>"
            f'<h1>Code Review Ledger</h1><p class="sub">Which reviewers find real problems, and what they cost. Built {built}.</p>')
    if not runs:
        return (head + f'<div class="panel empty" style="margin-top:24px">No reviews recorded yet in '
                f"{escape(str(folder))}. Run a review to add the first.</div></main></body></html>")
    rows = summarise(runs)
    all_rows = rows.values()
    blocking = sum(r["blocking"] for r in all_rows)
    pbi = sum(r["pbi"] for r in all_rows)
    dropped = sum(r["dropped"] for r in all_rows)
    changes = sum(1 for r in runs if r.get("verdict") == "request-changes")
    stats = [(len(runs), "reviews"), (changes, "requested changes"), (blocking, "Critical or Major reported"),
             (pbi, "moved to another PBI"), (dropped, "dropped as wrong")]
    stat_html = "".join(f"<div><b>{n}</b><span>{label}</span></div>" for n, label in stats)

    order = sorted(rows.items(), key=lambda kv: (-kv[1]["runs"], kv[0]))
    table = "".join(reviewer_row(name, row) for name, row in order)
    reviewers = (
        '<h2>Reviewers</h2><div class="panel"><table><thead><tr><th>Reviewer</th><th>Runs</th><th>Skipped</th>'
        "<th>Critical + Major</th><th>Reported</th><th>Another PBI</th><th>Left out</th><th>Dropped</th>"
        '<th>Held up</th><th>Avg tokens</th><th>Avg time</th><th>Tokens per finding</th><th class="left">Findings</th>'
        f"</tr></thead><tbody>{table}</tbody></table></div>"
        '<div class="legend"><span><i class="kept"></i>Reported</span><span><i class="pbi"></i>Another PBI</span>'
        '<span><i class="dropped"></i>Dropped</span></div>'
        '<p class="note">Held up is the share of findings that survived verification. '
        "Left out means Minors and nits kept out of the report. A dash means no review recorded what it dropped.</p>")

    topics = ad_hoc_topics(runs)
    ad_hoc = ""
    if topics:
        body = "".join(f"<tr><td>{escape(t)}</td><td>{n}</td><td>{found}</td></tr>" for t, (n, found) in topics)
        ad_hoc = ('<h2>Ad Hoc questions</h2><div class="panel"><table style="min-width:360px"><thead><tr>'
                  f"<th>Topic</th><th>Runs</th><th>Findings</th></tr></thead><tbody>{body}</tbody></table></div>")

    recent = "".join(run_row(run) for run in runs[:RECENT])
    latest = (f'<h2>Latest {min(RECENT, len(runs))} reviews</h2><div class="panel"><table><thead><tr>'
              '<th>When</th><th class="left">Reviewed</th><th class="left">Caller</th><th class="left">Verdict</th>'
              "<th>Reviewers</th><th>Reported</th><th>Another PBI</th><th>Dropped</th><th>Tokens</th>"
              f"</tr></thead><tbody>{recent}</tbody></table></div>")
    return (f'{head}<div class="stats">{stat_html}</div>{reviewers}{ad_hoc}{latest}</main></body></html>')


def build(out=None):
    """Writes the page and returns its path. record.py calls this after every save."""
    folder = ledger_dir()
    folder.mkdir(parents=True, exist_ok=True)
    out = out or folder / "reviews.html"
    out.write_text(render(load_runs(folder), folder))
    return out


def main():
    out = Path(sys.argv[2]) if len(sys.argv) == 3 and sys.argv[1] == "--out" else None
    print(build(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
