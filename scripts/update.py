#!/usr/bin/env python3
"""Rebuilds README.md, INTERNATIONAL.md and data/internships.json from the lists SpaceJobs.Now publishes every night.

SpaceJobs.Now reads each space company's own careers site nightly and publishes its internship and co-op lists as
public files. This script reads those files, joins them into one list and writes the tables. Standard library only.
Run: python3 scripts/update.py
"""
import datetime as dt
import json
import os
import urllib.request

STORE = "https://v4jmgkewgmoxqrya.public.blob.vercel-storage.com/internship-pages"
SITE = "https://spacejobs.now"
TAG = "utm_source=github&utm_medium=internship-list"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

TERMS = {"summer-2027": "Summer 2027", "spring-2027": "Spring 2027", "winter-2027": "Winter 2027", "fall-2027": "Fall 2027",
         "summer-2026": "Summer 2026", "fall-2026": "Fall 2026", "winter-2026": "Winter 2026", "spring-2028": "Spring 2028", "summer-2028": "Summer 2028"}
FIELDS = [
    ("ground-software", "Software and IT"), ("gnc-flight-software", "Flight software and GNC"),
    ("mechanical-structures", "Mechanical, structures and thermal"), ("avionics-electrical", "Avionics and electrical"),
    ("rf-communications", "RF, communications and payloads"), ("propulsion", "Propulsion"),
    ("systems-test", "Systems, integration and test"), ("launch-mission-ops", "Launch and mission operations"),
    ("manufacturing", "Manufacturing"), ("quality-safety", "Quality and mission assurance"),
    ("science-imaging", "Science, imaging and Earth data"), ("business-programs", "Business and programs"),
    ("supply-chain-facilities", "Supply chain and facilities"),
]
STATE_NAMES = {"AL": "alabama", "AZ": "arizona", "CA": "california", "CO": "colorado", "FL": "florida", "MD": "maryland",
               "NM": "new-mexico", "PA": "pennsylvania", "TX": "texas", "VA": "virginia", "WA": "washington"}


def get(name):
    req = urllib.request.Request(f"{STORE}/{name}.json", headers={"User-Agent": "spacejobsnow-github-list"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def link(path):
    return f"{SITE}{path}{'&' if '?' in path else '?'}{TAG}"


def cell(text):
    return (text or "").replace("|", "/").replace("\n", " ").strip()


def in_us(job):
    return bool(job.get("states")) or bool(job.get("inUs")) or "United States" in (job.get("place") or "")


def term(job):
    return ", ".join(TERMS.get(f, f) for f in (job.get("facets") or []))


def posted(job):
    try:
        return dt.datetime.fromisoformat(job["postedAt"].replace("Z", "+00:00")).strftime("%b %-d")
    except Exception:
        return ""


def rows(jobs):
    out = ["| Company | Role | Location | Pay | Term | Posted |", "|---|---|---|---|---|---|"]
    for j in jobs:
        out.append(f"| **{cell(j['company'])}** | [{cell(j['title'])}]({link(j['path'])}) | {cell(j.get('place'))} | {cell(j.get('pay'))} | {term(j)} | {posted(j)} |")
    return out


def main():
    index = get("index")
    names = [f"kind-{k['kind']}" for k in index["kinds"]] + [s["code"] for s in index["states"]] + [f"facet-{f['facet']}" for f in index.get("facets", [])]
    jobs = {}
    for name in names:
        for j in get(name).get("jobs") or []:
            if j.get("path") and j.get("title"):
                jobs[j["path"]] = j
    if len(jobs) < 100:
        raise SystemExit(f"only {len(jobs)} internships read: keeping the last list")
    ordered = sorted(jobs.values(), key=lambda j: (j.get("postedAt") or "", j["company"]), reverse=True)
    us = [j for j in ordered if in_us(j)]
    abroad = [j for j in ordered if not in_us(j)]
    companies = len({j["employer"] for j in ordered})
    today = dt.datetime.now(dt.timezone.utc).strftime("%-d %b %Y")
    summer = sum(1 for j in ordered if "summer-2027" in (j.get("facets") or []))
    kinds = {k["kind"]: k["jobs"] for k in index["kinds"]}
    states = {s["code"]: s["jobs"] for s in index["states"]}

    head = [
        "# Summer 2027 Space and Aerospace Internships",
        "",
        f"Every open internship and co-op at space companies, read each night from the company's own careers site by [SpaceJobs.Now]({link('/space-internships')}), a free job board for the space industry.",
        "",
        f"**{len(us)} open in the United States, {len(abroad)} in Europe, Canada and Asia-Pacific, at {companies} companies. {summer} name Summer 2027 so far. Updated {today}.**",
        "",
        "A role is added when the company posts it and taken off when the company takes it down. Pay is shown only where the posting states it. Each role opens its page on SpaceJobs.Now with the full posting, who may apply and how.",
        "",
        "- United States: the table below",
        f"- [Europe, Canada and Asia-Pacific](INTERNATIONAL.md): ESA, Airbus, Thales Alenia Space, ArianeGroup, DLR, CNES, OHB and more ({len(abroad)} roles)",
        "- The same list as data: [data/internships.json](data/internships.json) (CC BY 4.0)",
        "",
        "Many US roles require US citizenship or US person status (export rules); each role's page says so.",
        "",
        "## By field",
        "",
    ]
    head += [f"- [{label}]({link('/space-internships/' + slug)}) ({kinds[slug]})" for slug, label in FIELDS if kinds.get(slug)]
    head += ["", "## By state", ""]
    head.append(", ".join(f"[{code}]({link('/space-internships/' + STATE_NAMES[code])}) ({n})" for code, n in sorted(states.items(), key=lambda s: -s[1]) if code in STATE_NAMES))
    head += [
        "",
        "## Guides",
        "",
        f"- [How to get a space internship (2027)]({link('/learn/how-to-get-a-space-internship')})",
        f"- [Summer 2027]({link('/space-internships/summer-2027')}), [Spring 2027]({link('/space-internships/spring-2027')}) and [Winter 2027]({link('/space-internships/winter-2027')}) lists",
        f"- [Entry-level space jobs for new graduates]({link('/space-jobs-no-experience')})",
        "",
        f"## United States ({len(us)})",
        "",
    ]
    foot = [
        "",
        "## Missing a company?",
        "",
        "Open an issue with the company's careers page and we look at adding it to the nightly read.",
        "",
        "The list is free to reuse with credit to SpaceJobs.Now (CC BY 4.0).",
        "",
    ]
    with open(os.path.join(ROOT, "README.md"), "w") as f:
        f.write("\n".join(head + rows(us) + foot))
    intl = [
        "# Space internships in Europe, Canada and Asia-Pacific",
        "",
        f"{len(abroad)} open internships, traineeships and student roles outside the United States, read each night from the company's own careers site by [SpaceJobs.Now]({link('/space-internships')}). Updated {today}.",
        "",
        "[Back to the United States list](README.md)",
        "",
    ]
    with open(os.path.join(ROOT, "INTERNATIONAL.md"), "w") as f:
        f.write("\n".join(intl + rows(abroad) + [""]))
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    data = [{"company": j["company"], "title": j["title"], "location": j.get("place"), "in_us": in_us(j), "states": j.get("states") or [],
             "pay": j.get("pay"), "term": term(j) or None, "field": j.get("kind"), "posted": (j.get("postedAt") or "")[:10], "url": link(j["path"])} for j in ordered]
    with open(os.path.join(ROOT, "data", "internships.json"), "w") as f:
        json.dump({"source": "SpaceJobs.Now (https://spacejobs.now)", "license": "CC BY 4.0", "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"), "internships": data}, f, indent=1)
    print(f"{len(us)} US, {len(abroad)} abroad, {companies} companies")


if __name__ == "__main__":
    main()
