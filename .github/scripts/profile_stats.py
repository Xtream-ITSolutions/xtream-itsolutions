"""Erzeugt eine ausfallsichere GitHub-Kennzahlen-Grafik (SVG) fuer das Org-Profil.

Liest die oeffentlichen Repositories der Organisation ueber die GitHub-REST-API
und schreibt `profile-stats.svg`. Keine externen Bilddienste noetig — die Datei
wird per GitHub Action in den `output`-Branch gelegt und im README eingebunden.

Aufruf:
    GH_TOKEN=<token> python profile_stats.py [--org Xtream-ITSolutions] [--out profile-stats.svg]
"""

import argparse
import collections
import datetime
import json
import os
import sys
import urllib.request

API = "https://api.github.com"


def api_get(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_public_repos(org, token):
    repos = []
    page = 1
    while True:
        batch = api_get(f"{API}/orgs/{org}/repos?per_page=100&type=public&page={page}", token)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def build_svg(repo_count, star_count, top_languages, updated):
    langs = " · ".join(top_languages) if top_languages else "–"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="228" role="img" aria-label="GitHub Kennzahlen">
  <rect x="1" y="1" width="798" height="226" rx="12" fill="#0d1117" stroke="#007eff" stroke-width="2"/>
  <text x="36" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="bold" fill="#ffffff">Xtream-ITSolutions auf GitHub</text>
  <text x="36" y="72" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#8b949e">Automatisch erzeugt — ohne externen Statistikdienst</text>
  <g font-family="Segoe UI, Arial, sans-serif">
    <text x="36" y="128" font-size="40" font-weight="bold" fill="#007eff">{repo_count}</text>
    <text x="36" y="152" font-size="14" fill="#8b949e">ffentliche Repos</text>
    <text x="330" y="128" font-size="40" font-weight="bold" fill="#007eff">{star_count}</text>
    <text x="330" y="152" font-size="14" fill="#8b949e">Stars gesamt</text>
    <text x="560" y="128" font-size="20" font-weight="bold" fill="#ffffff">{langs}</text>
    <text x="560" y="152" font-size="14" fill="#8b949e">Top-Sprachen</text>
  </g>
  <text x="36" y="196" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#6e7681">Stand: {updated} (UTC) · github.com/Xtream-ITSolutions</text>
</svg>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", default="Xtream-ITSolutions")
    parser.add_argument("--out", default="profile-stats.svg")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN", "")
    try:
        repos = fetch_public_repos(args.org, token)
    except Exception as exc:  # API-Fehler: alte Grafik behalten, Job nicht scheitern lassen
        print(f"GitHub-API nicht erreichbar ({exc}); alte Grafik wird behalten.")
        return 0

    stars = sum(r.get("stargazers_count", 0) for r in repos)
    langs = collections.Counter(r.get("language") for r in repos if r.get("language"))
    top = [lang for lang, _ in langs.most_common(3)]
    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(build_svg(len(repos), stars, top, updated))
    print(f"{args.out} geschrieben: {len(repos)} Repos, {stars} Stars, Top: {top or '–'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
