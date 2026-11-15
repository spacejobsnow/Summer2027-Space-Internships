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
# The internship program guides on SpaceJobs.Now (deadlines, pay, who may apply and how), read from each program's own
# pages. A deadline is shown only while it is ahead.
GUIDES = [
    ("NASA internships", "/employers/nasa", "2027-03-01", "Summer 2027 applications"),
    ("NASA JPL internships", "/employers/jpl/internships", "2027-03-12", "Summer 2027 applications"),
    ("ESA internships (ESA member state citizens)", "/employers/esa/internships", "2026-11-30", "2027 student internships"),
    ("SpaceX internships", "/employers/spacex/internships", None, None),
    ("Blue Origin internships", "/employers/blue-origin/internships", None, None),
    ("Lockheed Martin internships", "/employers/lockheed-martin/internships", None, None),
    ("Northrop Grumman internships", "/employers/northrop-grumman", None, None),
    ("Boeing internships", "/employers/boeing", None, None),
    ("Rocket Lab internships", "/employers/rocket-lab/internships", None, None),
    ("The Aerospace Corporation internships", "/employers/aerospace-corporation/internships", None, None),
    ("ULA internships", "/employers/united-launch-alliance/internships", None, None),
    ("Firefly Aerospace internships", "/employers/firefly-aerospace/internships", None, None),
    ("Axiom Space internships", "/employers/axiom-space/internships", None, None),
    ("Varda internships", "/employers/varda/internships", None, None),
    ("Impulse Space internships", "/employers/impulse-space/internships", None, None),
    ("Muon Space internships", "/employers/muon-space/internships", None, None),
    ("Astranis internships", "/employers/astranis/internships", None, None),
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


STATE_LABEL = {"AL": "Alabama", "AZ": "Arizona", "CA": "California", "CO": "Colorado", "FL": "Florida", "MD": "Maryland",
               "NM": "New Mexico", "PA": "Pennsylvania", "TX": "Texas", "VA": "Virginia", "WA": "Washington"}


def page(path, title, description, lines):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    front = ["---", f"title: \"{title}\"", f"description: \"{description}\"", "---", ""]
    with open(full, "w") as f:
        f.write("\n".join(front + lines + [""]))


PAGES_BASE = "https://spacejobsnow.github.io/Summer2027-Space-Internships/"


def write_pages(by_field, by_state, today, us_all):
    """One page per field and per state (US roles only), so a search for propulsion internships or space internships in
    Texas finds a list of exactly those; every row opens the role's page on SpaceJobs.Now."""
    for slug, label in FIELDS:
        jobs = by_field.get(slug) or []
        if not jobs:
            continue
        companies = sorted({j["company"] for j in jobs}, key=lambda c: -sum(1 for j in jobs if j["company"] == c))
        title = f"{label} internships at space companies (2027)"
        desc = f"{len(jobs)} open {label.lower()} internships and co-ops at space companies in the US ({', '.join(companies[:4])} and more), updated daily."
        page(f"fields/{slug}.md", title, desc, [
            f"# {title}", "",
            f"**{len(jobs)} open in the United States at {len(companies)} companies, most at {', '.join(companies[:5])}. Updated {today}.**", "",
            f"Read each night from each company's own careers site by [SpaceJobs.Now]({link('/space-internships/' + slug)}), which shows the same list with pay, filters and the full postings. Many roles require US citizenship or US person status (export rules); each role's page says so.", "",
            "[All space internships](../README.md) · [By state](../README.md#by-state) · [Europe, Canada and Asia-Pacific](../INTERNATIONAL.md)", "",
        ] + rows(jobs))
    written = [f"fields/{slug}" for slug, _ in FIELDS if by_field.get(slug)]
    for code, jobs in by_state.items():
        if not jobs:
            continue
        written.append(f"states/{STATE_NAMES[code]}")
        name = STATE_LABEL[code]
        companies = sorted({j["company"] for j in jobs}, key=lambda c: -sum(1 for j in jobs if j["company"] == c))
        title = f"Space and aerospace internships in {name} (2027)"
        desc = f"{len(jobs)} open space internships and co-ops in {name} ({', '.join(companies[:4])} and more), updated daily."
        page(f"states/{STATE_NAMES[code]}.md", title, desc, [
            f"# {title}", "",
            f"**{len(jobs)} open at {len(companies)} companies, most at {', '.join(companies[:5])}. Updated {today}.**", "",
            f"Read each night from each company's own careers site by [SpaceJobs.Now]({link('/space-internships/' + STATE_NAMES[code])}), which shows the same list with pay, filters and the full postings. Many roles require US citizenship or US person status (export rules); each role's page says so.", "",
            "[All space internships](../README.md) · [By field](../README.md#by-field) · [Europe, Canada and Asia-Pacific](../INTERNATIONAL.md)", "",
        ] + rows(jobs))
    written += write_company_pages(us_all, today)
    with open(os.path.join(ROOT, "data", "pages.txt"), "w") as f:
        f.write("\n".join([PAGES_BASE, PAGES_BASE + "INTERNATIONAL"] + [PAGES_BASE + w for w in written]) + "\n")


def write_company_pages(us, today):
    """One page per company with five or more open US internships ("SpaceX internships 2027"), the search people make most
    for an employer; it links the company's program guide on SpaceJobs.Now (how to apply, deadlines, who may apply)."""
    by_company = {}
    for j in us:
        by_company.setdefault(j["employer"], []).append(j)
    guides = {path.split("/")[2]: path for _, path, _, _ in GUIDES if path.startswith("/employers/")}
    written, listed = [], []
    for slug, jobs in sorted(by_company.items(), key=lambda x: -len(x[1])):
        if len(jobs) < 5:
            continue
        name = jobs[0]["company"]
        jobs = sorted(jobs, key=lambda j: j.get("postedAt") or "", reverse=True)
        fields = sorted({j.get("kind") for j in jobs if j.get("kind")}, key=lambda k: -sum(1 for j in jobs if j.get("kind") == k))
        labels = dict(FIELDS)
        title = f"{name} internships 2027: open roles, pay and how to apply"
        desc = f"{len(jobs)} open {name} internships and co-ops in the US ({', '.join(labels.get(f, f) for f in fields[:3]).lower()}), updated daily."
        guide = f"/employers/{slug}/internships"
        page(f"companies/{slug}.md", title, desc, [
            f"# {name} internships (2027)", "",
            f"**{len(jobs)} open in the United States. Updated {today}.**", "",
            f"How {name}'s internship program works, who may apply and when: [{name} internships on SpaceJobs.Now]({link(guide)}). Each role below opens its full posting there, with how to apply. Many roles require US citizenship or US person status (export rules); each role's page says so.", "",
            "[All space internships](../README.md) · [By field](../README.md#by-field) · [By state](../README.md#by-state)", "",
        ] + rows(jobs))
        written.append(f"companies/{slug}")
        listed.append((name, slug, len(jobs)))
    with open(os.path.join(ROOT, "data", "companies.txt"), "w") as f:
        f.write("\n".join(f"{n}\t{s}\t{c}" for n, s, c in listed) + "\n")
    return written


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
        "- Graduating? Entry-level roles have their own list: [New-Grad-Space-Jobs](https://github.com/spacejobsnow/New-Grad-Space-Jobs)",
        "- The same list as data: [data/internships.json](data/internships.json) (CC BY 4.0)",
        "",
        "Many US roles require US citizenship or US person status (export rules); each role's page says so.",
        "",
        "## By field",
        "",
    ]
    us_by_field = {slug: [j for j in us if j.get("kind") == slug] for slug, _ in FIELDS}
    us_by_state = {code: [j for j in us if code in (j.get("states") or [])] for code in STATE_NAMES}
    head += [f"- [{label}](fields/{slug}.md) ({len(us_by_field[slug])} in the US)" for slug, label in FIELDS if us_by_field.get(slug)]
    head += ["", "## By state", ""]
    head.append(", ".join(f"[{STATE_LABEL[code]}](states/{STATE_NAMES[code]}.md) ({len(us_by_state[code])})" for code in sorted(us_by_state, key=lambda c: -len(us_by_state[c])) if us_by_state[code]))
    head += ["", "## By company", ""]
    by_emp = {}
    for j in us:
        by_emp.setdefault(j["employer"], []).append(j)
    head.append(", ".join(f"[{v[0]['company']}](companies/{k}.md) ({len(v)})" for k, v in sorted(by_emp.items(), key=lambda x: -len(x[1])) if len(v) >= 5))
    today_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    deadlines = sorted((d, name, path, what) for name, path, d, what in GUIDES if d and d >= today_iso)
    if deadlines:
        head += ["", "## Deadlines ahead", ""]
        head += [f"- **{dt.date.fromisoformat(d).strftime('%-d %b %Y')}**: [{name}]({link(path)}), {what}" for d, name, path, what in deadlines]
    head += ["", "## Program guides", "", "How each program works, what it pays and who may apply, read from the employer's own pages:", ""]
    head.append(", ".join(f"[{name.replace(' internships', '')}]({link(path)})" for name, path, d, what in GUIDES))
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
    write_pages(us_by_field, us_by_state, today, us)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    data = [{"company": j["company"], "title": j["title"], "location": j.get("place"), "in_us": in_us(j), "states": j.get("states") or [],
             "pay": j.get("pay"), "term": term(j) or None, "field": j.get("kind"), "posted": (j.get("postedAt") or "")[:10], "url": link(j["path"])} for j in ordered]
    with open(os.path.join(ROOT, "data", "internships.json"), "w") as f:
        json.dump({"source": "SpaceJobs.Now (https://spacejobs.now)", "license": "CC BY 4.0", "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"), "internships": data}, f, indent=1)
    print(f"{len(us)} US, {len(abroad)} abroad, {companies} companies")


if __name__ == "__main__":
    main()
