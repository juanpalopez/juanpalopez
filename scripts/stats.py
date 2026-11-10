#!/usr/bin/env python3
"""Render assets/stats.svg from the last year of GitHub contributions.

Usage: GH_TOKEN=... python3 scripts/stats.py <login>
       python3 scripts/stats.py --sample   (fake numbers, for previewing the design)
"""
import json, os, sys, urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
  totalCommitContributions totalPullRequestContributions
  totalPullRequestReviewContributions totalIssueContributions
  restrictedContributionsCount contributionCalendar{totalContributions}}}}"""


def fetch(login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "User-Agent": "profile-stats"},
    )
    body = json.load(urllib.request.urlopen(req, timeout=30))
    if body.get("errors"):
        sys.exit(f"GitHub API error: {body['errors']}")
    c = body["data"]["user"]["contributionsCollection"]
    return {
        "commits": c["totalCommitContributions"],
        "prs": c["totalPullRequestContributions"],
        "reviews": c["totalPullRequestReviewContributions"],
        "issues": c["totalIssueContributions"],
        "private": c["restrictedContributionsCount"],
        "total": c["contributionCalendar"]["totalContributions"],
    }


def render(s):
    BG, FG, MUTED, ACC, LINE = "#0d1117", "#f0f6fc", "#8b949e", "#3ddc97", "#30363d"
    mono = 'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"'
    sans = 'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"'
    tiles = [("commits", "commits"), ("reviews", "code reviews"), ("prs", "pull requests"), ("issues", "issues")]
    out = []
    for i, (k, label) in enumerate(tiles):
        x, y = 60 + (i % 2) * 220, 118 + (i // 2) * 78
        out.append(f'<text x="{x}" y="{y}" {sans} font-size="40" font-weight="800" fill="{FG}" letter-spacing="-1">{s[k]:,}</text>')
        out.append(f'<text x="{x}" y="{y + 24}" {mono} font-size="15" fill="{MUTED}">{label}</text>')

    # Diamond, same axes as GitHub's activity overview: review top, issues right, PRs bottom, commits left
    cx, cy, R = 700, 142, 78
    four = [s["reviews"], s["issues"], s["prs"], s["commits"]]
    tot = sum(four) or 1
    pct = [v / tot for v in four]
    top = max(pct) or 1
    r = [R * (0.08 + 0.92 * p / top) for p in pct]
    pts = [(cx, cy - r[0]), (cx + r[1], cy), (cx, cy + r[2]), (cx - r[3], cy)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{ACC}"/>' for x, y in pts)
    lab = lambda x, y, anchor, name, p: (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" {mono} font-size="13" fill="{MUTED}">'
        f'<tspan fill="{FG}">{round(p * 100)}%</tspan> {name}</text>')
    labels = (lab(cx, cy - R - 12, "middle", "review", pct[0]) + lab(cx + R + 10, cy - 8, "start", "issues", pct[1])
              + lab(cx, cy + R + 22, "middle", "pull requests", pct[2]) + lab(cx - R - 10, cy - 8, "end", "commits", pct[3]))
    private = f" · {s['private']:,} in private repos" if s["private"] else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 290" width="900" role="img" aria-label="Last year on GitHub: {s['commits']} commits, {s['reviews']} code reviews, {s['prs']} pull requests, {s['issues']} issues.">
<style>.shape{{transform-origin:{cx}px {cy}px;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}}@keyframes grow{{from{{transform:scale(0)}}}}@media (prefers-reduced-motion:reduce){{.shape{{animation:none}}}}</style>
<rect x=".75" y=".75" width="898.5" height="288.5" rx="18" fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>
<text x="60" y="56" {mono} font-size="17" fill="{MUTED}"><tspan fill="{ACC}">~/juanpalopez</tspan> $ git shortlog --since=1.year</text>
{''.join(out)}
<text x="60" y="262" {mono} font-size="14" fill="{MUTED}">{s['total']:,} contributions in the last year{private}</text>
<g stroke="{LINE}" stroke-width="1.5"><path d="M{cx - R} {cy}H{cx + R}M{cx} {cy - R}V{cy + R}"/></g>
<g class="shape"><polygon points="{poly}" fill="{ACC}" fill-opacity=".22" stroke="{ACC}" stroke-width="2" stroke-linejoin="round"/>{dots}</g>
{labels}
</svg>
'''


if __name__ == "__main__":
    if sys.argv[1:] == ["--sample"]:
        stats = {"commits": 1284, "prs": 212, "reviews": 467, "issues": 38, "private": 1630, "total": 2001}
        path = "stats-sample.svg"
    else:
        stats, path = fetch(sys.argv[1]), "assets/stats.svg"
    open(path, "w").write(render(stats))
    print(f"wrote {path}: {stats}")
