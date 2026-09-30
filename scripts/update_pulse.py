"""Generate an owned profile SVG from real public GitHub API data (no dependencies)."""
import collections
import datetime
import html
import json
import pathlib
import subprocess


def github(endpoint, paginate=False):
    command = ["gh", "api", endpoint]
    if paginate:
        command += ["--paginate", "--slurp"]
    return json.loads(subprocess.check_output(command, text=True))


def build(user, repos):
    original = [repo for repo in repos if not repo["fork"] and not repo.get("private")]
    languages = collections.Counter(repo["language"] for repo in original if repo.get("language"))
    stars = sum(repo["stargazers_count"] for repo in original)
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y")
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="330" viewBox="0 0 1000 330" role="img" aria-labelledby="title desc">', '<title id="title">Open-source pulse</title>', f'<desc id="desc">{len(original)} original public repositories, {stars} stars across those repositories, {user["followers"]} followers. Snapshot {today} UTC.</desc>', '<rect width="1000" height="330" rx="16" fill="#0e1b2b"/>', '<text x="34" y="39" fill="#5eead4" font-family="monospace" font-size="12" letter-spacing="2">OPEN-SOURCE / LIVE SNAPSHOT</text>', f'<text x="966" y="39" text-anchor="end" fill="#95aabd" font-family="monospace" font-size="11">{today.upper()} UTC</text>']
    for x, value, label in [(34, len(original), "ORIGINAL PUBLIC REPOS"), (365, stars, "STARS · ORIGINAL REPOS"), (697, user["followers"], "GITHUB FOLLOWERS")]:
        svg += [f'<text x="{x}" y="105" fill="#eff7ff" font-family="Arial,sans-serif" font-size="45" font-weight="700">{value}</text>', f'<text x="{x}" y="133" fill="#8ca7ba" font-family="monospace" font-size="11" letter-spacing="1">{label}</text>']
    svg += ['<path d="M34 162H966" stroke="#273a4b"/>', '<text x="34" y="194" fill="#a0b9cb" font-family="monospace" font-size="11">REPOSITORY LANGUAGES / ORIGINAL PUBLIC REPOS</text>']
    top = languages.most_common(4)
    total = max(sum(languages.values()), 1)
    x = 34
    palette = ["#5eead4", "#38bdf8", "#a5b4fc", "#fbbf24", "#52677d"]
    entries = top + ([("Other", sum(languages.values()) - sum(count for _, count in top))] if len(languages) > 4 else [])
    for i, (language, count) in enumerate(entries):
        width = count / total * 930
        svg.append(f'<rect x="{x:.2f}" y="216" width="{width:.2f}" height="13" fill="{palette[i]}"/>')
        x += width
        label_x = 34 + i * 185
        svg += [f'<circle cx="{label_x}" cy="257" r="4" fill="{palette[i]}"/>', f'<text x="{label_x + 11}" y="261" fill="#c1d4e2" font-family="Arial,sans-serif" font-size="12">{html.escape(language)} · {count}</text>']
    svg += ['<text x="34" y="302" fill="#7994a9" font-family="monospace" font-size="10">REAL PUBLIC DATA · UPDATED DAILY · NO THIRD-PARTY STATS SERVICE</text>', '</svg>']
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    user = github("users/Barbhuiya12")
    repos = [repo for page in github("users/Barbhuiya12/repos?per_page=100&type=owner", paginate=True) for repo in page]
    target = pathlib.Path(__file__).resolve().parents[1] / "assets" / "github-pulse.svg"
    target.write_text(build(user, repos), encoding="utf-8")
    print("Updated public GitHub snapshot.")
