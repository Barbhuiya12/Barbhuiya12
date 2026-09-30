"""Render the actual GitHub contribution calendar as a locally hosted SVG."""
import datetime
import json
import pathlib
import subprocess

QUERY = '''query {
  user(login: "Barbhuiya12") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
  }
}'''


def build(calendar):
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y")
    weeks = calendar["weeks"]
    cell = min(16, 880 / max(len(weeks), 1))
    size = cell - 3
    palette = ["#1e3040", "#164e49", "#167c6b", "#20b599", "#5eead4"]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="285" viewBox="0 0 1000 285" role="img" aria-labelledby="title desc">', '<title id="title">GitHub Activity</title>', f'<desc id="desc">{calendar["totalContributions"]} contributions in the GitHub calendar. Updated {today} UTC.</desc>', '<rect width="1000" height="285" rx="16" fill="#0e1b2b"/>', '<text x="34" y="40" fill="#5eead4" font-family="monospace" font-size="13" letter-spacing="2">GITHUB ACTIVITY</text>', f'<text x="966" y="40" text-anchor="end" fill="#95aabd" font-family="monospace" font-size="11">{today.upper()} UTC</text>', f'<text x="34" y="74" fill="#eff7ff" font-family="Arial,sans-serif" font-size="19">{calendar["totalContributions"]:,} contributions in the past year</text>']
    last_month = None
    for column, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = datetime.date.fromisoformat(day["date"])
            if date.month != last_month:
                if column < len(weeks) - 2:
                    svg.append(f'<text x="{86 + column * cell:.2f}" y="108" fill="#9bb0c3" font-family="Arial,sans-serif" font-size="10">{date.strftime("%b")}</text>')
                last_month = date.month
            count = day["contributionCount"]
            level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 5 else 3 if count <= 9 else 4
            x, y = 86 + column * cell, 120 + day["weekday"] * cell
            svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" rx="2" fill="{palette[level]}"><title>{day["date"]}: {count} contributions</title></rect>')
    for label, weekday in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        svg.append(f'<text x="34" y="{130 + weekday * cell:.2f}" fill="#9bb0c3" font-family="Arial,sans-serif" font-size="10">{label}</text>')
    svg.append('<text x="34" y="261" fill="#7994a9" font-family="monospace" font-size="10">REAL CONTRIBUTIONS · DAILY REFRESH · GITHUB VISIBILITY RULES APPLY</text>')
    svg.append('<text x="804" y="261" fill="#9bb0c3" font-family="Arial,sans-serif" font-size="10">Less</text>')
    for i, color in enumerate(palette):
        svg.append(f'<rect x="{836 + i * 17}" y="250" width="13" height="13" rx="2" fill="{color}"/>')
    svg += ['<text x="928" y="261" fill="#9bb0c3" font-family="Arial,sans-serif" font-size="10">More</text>', '</svg>']
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    data = json.loads(subprocess.check_output(["gh", "api", "graphql", "-f", "query=" + QUERY], text=True))
    if data.get("errors"):
        raise RuntimeError("GitHub did not return a contribution calendar.")
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    target = pathlib.Path(__file__).resolve().parents[1] / "assets" / "github-activity.svg"
    target.write_text(build(calendar), encoding="utf-8")
    print("Updated GitHub activity calendar from actual contribution data.")
