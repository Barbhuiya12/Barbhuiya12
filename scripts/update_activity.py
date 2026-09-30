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


def streaks(calendar, today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    days = {datetime.date.fromisoformat(day["date"]): day["contributionCount"] for week in calendar["weeks"] for day in week["contributionDays"] if datetime.date.fromisoformat(day["date"]) <= today}
    current = longest = running = active = 0
    previous = None
    for date, count in sorted(days.items()):
        if count > 0:
            running = running + 1 if previous == date - datetime.timedelta(days=1) else 1
            active += 1
            longest = max(longest, running)
        else:
            running = 0
        previous = date
    # Today is still in progress: an empty today does not break yesterday's streak.
    cursor = today if days.get(today, 0) > 0 else today - datetime.timedelta(days=1)
    while days.get(cursor, 0) > 0:
        current += 1
        cursor -= datetime.timedelta(days=1)
    return current, longest, active


def build_stats(calendar, user, repos):
    current, longest, active = streaks(calendar)
    stars = sum(repo["stargazers_count"] for repo in repos if not repo["fork"] and not repo.get("private"))
    metrics = [(current, "CURRENT STREAK", "consecutive days"), (longest, "LONGEST STREAK", "within past-year calendar"), (calendar["totalContributions"], "CONTRIBUTIONS", "past-year calendar"), (active, "ACTIVE DAYS", "past-year calendar"), (stars, "REPOSITORY STARS", "original public repositories"), (user["followers"], "FOLLOWERS", "public GitHub profile")]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="320" viewBox="0 0 1000 320" role="img" aria-labelledby="title desc">', '<title id="title">GitHub streaks and stats</title>', '<desc id="desc">Real GitHub contribution streaks, contribution totals, active days, repository stars, and followers. Streaks are limited to the past-year calendar.</desc>', '<rect width="1000" height="320" rx="16" fill="#0e1b2b"/>', '<text x="34" y="38" fill="#5eead4" font-family="monospace" font-size="13" letter-spacing="2">CONSISTENCY / STREAKS &amp; STATS</text>']
    for i, (value, label, note) in enumerate(metrics):
        x, y = 34 + (i % 3) * 330, 90 + (i // 3) * 115
        color = "#5eead4" if i == 0 else "#38bdf8" if i == 1 else "#eff7ff"
        svg += [f'<text x="{x}" y="{y}" fill="#8ca7ba" font-family="monospace" font-size="11" letter-spacing="1">{label}</text>', f'<text x="{x}" y="{y + 46}" fill="{color}" font-family="Arial,sans-serif" font-size="40" font-weight="700">{value:,}</text>', f'<text x="{x}" y="{y + 69}" fill="#7994a9" font-family="Arial,sans-serif" font-size="11">{note}</text>']
    svg += ['<text x="34" y="301" fill="#7994a9" font-family="monospace" font-size="10">DAILY SNAPSHOT · TODAY MAY BE INCOMPLETE · NO INVENTED RANK OR SCORE</text>', '</svg>']
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    data = json.loads(subprocess.check_output(["gh", "api", "graphql", "-f", "query=" + QUERY], text=True))
    if data.get("errors"):
        raise RuntimeError("GitHub did not return a contribution calendar.")
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    target = pathlib.Path(__file__).resolve().parents[1] / "assets" / "github-activity.svg"
    target.write_text(build(calendar), encoding="utf-8")
    user = json.loads(subprocess.check_output(["gh", "api", "users/Barbhuiya12"], text=True))
    pages = json.loads(subprocess.check_output(["gh", "api", "users/Barbhuiya12/repos?per_page=100&type=owner", "--paginate", "--slurp"], text=True))
    repos = [repo for page in pages for repo in page]
    target.with_name("github-stats.svg").write_text(build_stats(calendar, user, repos), encoding="utf-8")
    print("Updated GitHub activity, streaks, and stats from actual public data.")
