"""Console-style GitHub profile card generator.

Usage:
    python today.py              # fetch live stats, write dark_mode.svg + light_mode.svg
    python today.py --preview    # render every theme with placeholder stats into previews/

Env vars (live mode):
    ACCESS_TOKEN  classic PAT with `repo` + `read:user` (needed for private repos)
    USER_NAME     GitHub login (default: KumKaShree)
"""
import datetime
import json
import os
import sys
import time
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------
# CONFIG - edit these
# --------------------------------------------------------------------------
USER = os.environ.get("USER_NAME") or "KumKaShree"   # `or` so an empty secret still falls back
BIRTHDAY = datetime.date(2001, 5, 29)
DARK_THEME = "catppuccin"      # pick from THEMES
LIGHT_THEME = "catppuccin"     # light variant of the same (or a different) family
INCLUDE_FORKS_IN_LOC = False

PROMPT_USER = "amit@kumkashree"
TAGLINE = "Indie dev. Ships things. Self-hosts everything."
INFO = [
    ("Role", "Backend Developer"),
    ("Uptime", "{uptime}"),
    ("Location", "Odisha, India"),
    ("Languages", "Python, Go, TypeScript"),
    ("Frameworks", "FastAPI, Gin, discordgo, discord.py, Next.js, Elysia"),
    ("Data", "PostgreSQL, Redis"),
    ("Deploy", "Docker, Traefik, Dokploy, Coolify"),
    ("Self-hosting", "WireGuard, Supabase, GlitchTip, Rybbit"),
    ("Learning", "Rust"),
]
PROJECT = {
    "name": "BotFragg/",
    "desc": "Your VALORANT store, account stats, and skin alerts, right inside Discord.",
    "meta": "Python | PostgreSQL | Docker | github.com/BotFragg/BotFragg",
}
CONTACT = [
    ("GitHub", "github.com/KumKaShree"),
    ("Discord", "kumkashree"),
    ("Email", "ad7392182@gmail.com"),
]

BANNER = [
    "██╗  ██╗██╗   ██╗███╗   ███╗██╗  ██╗ █████╗ ███████╗██╗  ██╗██████╗ ███████╗███████╗",
    "██║ ██╔╝██║   ██║████╗ ████║██║ ██╔╝██╔══██╗██╔════╝██║  ██║██╔══██╗██╔════╝██╔════╝",
    "█████╔╝ ██║   ██║██╔████╔██║█████╔╝ ███████║███████╗███████║██████╔╝█████╗  █████╗  ",
    "██╔═██╗ ██║   ██║██║╚██╔╝██║██╔═██╗ ██╔══██║╚════██║██╔══██║██╔══██╗██╔══╝  ██╔══╝  ",
    "██║  ██╗╚██████╔╝██║ ╚═╝ ██║██║  ██╗██║  ██║███████║██║  ██║██║  ██║███████╗███████╗",
    "╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝",
]
BANNER_COLORS = ("#00d2ff", "#3a7bd5", "#00f5a0")        # dark mode gradient (left -> right)
BANNER_COLORS_LIGHT = ("#0891b2", "#3a7bd5", "#059669")  # darker, readable on light backgrounds
BANNER_FONT = 16      # banner font size
BANNER_STEP = 16      # banner line spacing (tight, so block glyphs connect)
BANNER_W = 806.4      # banner pixel width

# --------------------------------------------------------------------------
# THEMES: (dark, light) palettes
# keys: bg bar fg dim key accent ok num
# --------------------------------------------------------------------------
def P(bg, bar, fg, dim, key, accent, ok, num):
    return dict(bg=bg, bar=bar, fg=fg, dim=dim, key=key, accent=accent, ok=ok, num=num)

THEMES = {
    "dracula": (
        P("#282a36", "#1e1f29", "#f8f8f2", "#6272a4", "#ff79c6", "#bd93f9", "#50fa7b", "#f1fa8c"),
        P("#fffbeb", "#cfcfde", "#1f1f1f", "#6c664b", "#a3144d", "#644ac9", "#14710a", "#846e15"),
    ),
    "catppuccin": (
        P("#1e1e2e", "#181825", "#cdd6f4", "#6c7086", "#f5c2e7", "#cba6f7", "#a6e3a1", "#f9e2af"),
        P("#eff1f5", "#dce0e8", "#4c4f69", "#9ca0b0", "#ea76cb", "#8839ef", "#40a02b", "#df8e1d"),
    ),
    "tokyo-night": (
        P("#1a1b26", "#16161e", "#c0caf5", "#565f89", "#7aa2f7", "#bb9af7", "#9ece6a", "#e0af68"),
        P("#e1e2e7", "#d0d5e3", "#3760bf", "#848cb5", "#2e7de9", "#9854f1", "#587539", "#8c6c3e"),
    ),
    "gruvbox": (
        P("#282828", "#1d2021", "#ebdbb2", "#928374", "#fabd2f", "#fe8019", "#b8bb26", "#d3869b"),
        P("#fbf1c7", "#ebdbb2", "#3c3836", "#928374", "#b57614", "#af3a03", "#79740e", "#8f3f71"),
    ),
    "nord": (
        P("#2e3440", "#242933", "#d8dee9", "#616e88", "#88c0d0", "#81a1c1", "#a3be8c", "#ebcb8b"),
        P("#eceff4", "#d8dee9", "#2e3440", "#7b88a1", "#5e81ac", "#b48ead", "#5e8a4a", "#b07d2b"),
    ),
    "matrix": (
        P("#0d0d0d", "#000000", "#00ff41", "#008f11", "#39ff14", "#00ff41", "#00ff41", "#b6ffb6"),
        P("#f4fff4", "#d6f0d6", "#0a5c1a", "#4f8f5f", "#0b7a22", "#0b7a22", "#0b7a22", "#0b7a22"),
    ),
}

# --------------------------------------------------------------------------
# Layout constants (monospace grid; textLength pins each line to the grid so
# alignment survives whatever monospace font the viewer has)
# --------------------------------------------------------------------------
FONT_SIZE = 14
CW = 8.4          # char width
LH = 21           # line height
COLS = 100
PAD = 24
BAR_H = 38
WIDTH = int(PAD * 2 + COLS * CW)
KEYW = 15


# --------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------
def uptime(today=None):
    t = today or datetime.date.today()
    y = t.year - BIRTHDAY.year
    m = t.month - BIRTHDAY.month
    d = t.day - BIRTHDAY.day
    if d < 0:
        m -= 1
        prev_month_end = t.replace(day=1) - datetime.timedelta(days=1)
        d += prev_month_end.day
    if m < 0:
        y -= 1
        m += 12
    return f"{y} years, {m} months, {d} days"


def fetch_stats(user, token):
    import requests

    api = "https://api.github.com"
    headers = {"Authorization": f"bearer {token}", "Accept": "application/vnd.github+json"}

    def gql(query, variables):
        r = requests.post(f"{api}/graphql", json={"query": query, "variables": variables}, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(data["errors"])
        return data["data"]

    # profile + all repos the user owns / collaborates on / org-member of (private included)
    q = """
    query($login:String!, $cursor:String) {
      user(login:$login) {
        createdAt
        followers { totalCount }
        repositories(first:100, after:$cursor, ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]) {
          pageInfo { hasNextPage endCursor }
          nodes { nameWithOwner isFork stargazerCount owner { login } }
        }
      }
    }"""
    repos, cursor, created, followers = [], None, None, 0
    while True:
        u = gql(q, {"login": user, "cursor": cursor})["user"]
        created, followers = u["createdAt"], u["followers"]["totalCount"]
        repos += u["repositories"]["nodes"]
        if not u["repositories"]["pageInfo"]["hasNextPage"]:
            break
        cursor = u["repositories"]["pageInfo"]["endCursor"]

    owned = [r for r in repos if r["owner"]["login"].lower() == user.lower()]
    stars = sum(r["stargazerCount"] for r in owned)   # org-repo stars are added below, after we know where you contributed

    # commits: sum per calendar year (private ones counted via restrictedContributionsCount)
    cq = """
    query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) { contributionsCollection(from:$from, to:$to) {
        totalCommitContributions restrictedContributionsCount
        contributionCalendar { weeks { contributionDays { date contributionCount } } } } }
    }"""
    start_year = int(created[:4])
    now = datetime.datetime.now(datetime.timezone.utc)
    commits = 0
    days = {}   # date -> contribution count (all years)
    for yr in range(start_year, now.year + 1):
        frm = f"{yr}-01-01T00:00:00Z"
        to = f"{yr}-12-31T23:59:59Z" if yr < now.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")
        c = gql(cq, {"login": user, "from": frm, "to": to})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        for wk in c["contributionCalendar"]["weeks"]:
            for d in wk["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    # streaks (today not counted as a break if it has no contributions yet)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    cur, probe = 0, today
    if days.get(probe.isoformat(), 0) == 0:
        probe -= datetime.timedelta(days=1)
    while days.get(probe.isoformat(), 0) > 0:
        cur += 1
        probe -= datetime.timedelta(days=1)
    best = run = 0
    prev = None
    for ds in sorted(days):
        d = datetime.date.fromisoformat(ds)
        if days[ds] > 0:
            run = run + 1 if prev and (d - prev).days == 1 else 1
            best = max(best, run)
            prev = d
        elif prev is not None and (d - prev).days >= 1:
            run = 0

    # last push: newest PushEvent (private ones visible because the token is the user's own)
    last_push = None
    ev = requests.get(f"{api}/users/{user}/events", params={"per_page": 100}, headers=headers, timeout=60)
    if ev.status_code == 200:
        for e in ev.json():
            if e.get("type") == "PushEvent":
                dt = datetime.datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
                last_push = f"{dt.day} {dt:%b %Y}"
                break
    if last_push is None:   # fall back to the most recent day with contributions
        active = [k for k, v in days.items() if v > 0]
        if active:
            dt = datetime.date.fromisoformat(max(active))
            last_push = f"{dt.day} {dt:%b %Y}"

    # lines of code: per-repo contributor stats (cached, so a flaky 202 doesn't zero a repo)
    cache_path = os.path.join("cache", "loc.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
    add_total = del_total = 0
    org_stars = 0
    for r in repos:
        if r["isFork"] and not INCLUDE_FORKS_IN_LOC:
            continue
        nwo = r["nameWithOwner"]
        result = None
        for _ in range(6):
            resp = requests.get(f"{api}/repos/{nwo}/stats/contributors", headers=headers, timeout=60)
            if resp.status_code == 200:
                data = resp.json() or []
                mine = [c for c in data if c.get("author") and c["author"]["login"].lower() == user.lower()]
                a = sum(w["a"] for c in mine for w in c["weeks"])
                d = sum(w["d"] for c in mine for w in c["weeks"])
                result = [a, d]
                break
            if resp.status_code == 202:   # GitHub is computing stats; retry
                time.sleep(3)
                continue
            break
        if result is None:
            result = cache.get(nwo, [0, 0])
        cache[nwo] = result
        add_total += result[0]
        del_total += result[1]
        # stars from org/collaborator repos count only if you actually authored code in them
        if r["owner"]["login"].lower() != user.lower() and result[0] + result[1] > 0:
            org_stars += r["stargazerCount"]
    os.makedirs("cache", exist_ok=True)
    json.dump(cache, open(cache_path, "w", encoding="utf-8"), indent=1, sort_keys=True)

    return dict(repos=len(owned), stars=stars + org_stars, followers=followers, commits=commits,
                loc=add_total - del_total, add=add_total, dele=del_total,
                streak=cur, best_streak=best, last_push=last_push or "n/a")


PLACEHOLDER = dict(repos=42, stars=128, followers=64, commits=3210, loc=184320, add=251000, dele=66680,
                   streak=17, best_streak=64, last_push="6 Nov 2026")


# --------------------------------------------------------------------------
# SVG rendering
# --------------------------------------------------------------------------
def n(x):
    return f"{x:,}"


def build_lines(stats):
    """Each line = list of (text, class). Empty list = blank line."""
    ps = [(PROMPT_USER, "ok"), (" ~ % ", "accent")]
    lines = []

    lines.append([("> " + TAGLINE, "ok")])
    lines.append([])

    def prompt(cmd):
        lines.append(ps + [(cmd, "fg")])

    def kv(k, v, kw=KEYW, vcls="fg"):
        dots = "." * max(1, kw - len(k) - 1)
        lines.append([(" " + k + " ", "key"), (dots + " ", "dim"), (v, vcls)])

    prompt("./whoami")
    for k, v in INFO:
        kv(k, v.format(uptime=uptime()))
    lines.append([])

    prompt("./stats --all")
    # two-column rows
    def kv2(k1, v1, k2, v2):
        left = f" {k1} " + "." * max(1, KEYW - len(k1) - 1) + f" {v1}"
        pad = " " * max(2, 40 - len(left))
        lines.append([(" " + k1 + " ", "key"), ("." * max(1, KEYW - len(k1) - 1) + " ", "dim"), (v1, "num"),
                      (pad + k2 + " ", "key"), ("." * max(1, KEYW - len(k2) - 1) + " ", "dim"), (v2, "num")])
    kv2("Repos", n(stats["repos"]), "Stars", n(stats["stars"]))
    kv2("Commits", n(stats["commits"]), "Followers", n(stats["followers"]))
    kv2("Streak", f"{stats['streak']} days (best {stats['best_streak']})", "Last Push", stats["last_push"])
    lines.append([(" Lines of Code ", "key"), (". ", "dim"), (n(stats["loc"]), "num"),
                  ("  ( ", "dim"), (n(stats["add"]) + "++", "ok"), (", ", "dim"),
                  (n(stats["dele"]) + "--", "key"), (" )", "dim")])
    lines.append([])

    prompt("ls projects/")
    lines.append([(" " + PROJECT["name"], "accent")])
    lines.append([("   " + PROJECT["desc"], "fg")])
    lines.append([("   " + PROJECT["meta"], "dim")])
    lines.append([])

    prompt("cat contact.txt")
    for k, v in CONTACT:
        kv(k, v)
    lines.append([])

    lines.append(ps)  # final prompt; cursor is drawn after it
    return lines


def render(stats, palette, light=False):
    lines = build_lines(stats)
    banner_y0 = BAR_H + 36                       # first banner baseline
    banner_h = BANNER_STEP * len(BANNER)
    top = banner_y0 + banner_h + 10              # first body baseline
    height = int(top + len(lines) * LH + 12)
    c = palette
    bc = BANNER_COLORS_LIGHT if light else BANNER_COLORS
    banner_tspans = "".join(
        f'<tspan x="{PAD}" y="{banner_y0 + i * BANNER_STEP}" textLength="{BANNER_W}" lengthAdjust="spacingAndGlyphs">{escape(line.ljust(85))}</tspan>'
        for i, line in enumerate(BANNER))
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(USER)} console profile">')
    out.append(f"""<defs>
<linearGradient id="bg" gradientUnits="userSpaceOnUse" x1="{PAD}" y1="0" x2="{PAD + BANNER_W}" y2="0">
<stop offset="0" stop-color="{bc[0]}"/><stop offset="0.5" stop-color="{bc[1]}"/><stop offset="1" stop-color="{bc[2]}"/>
</linearGradient>
<linearGradient id="bs" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="bt"><text font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace" font-size="{BANNER_FONT}" xml:space="preserve">{banner_tspans}</text></clipPath>
<clipPath id="r"><rect width="{WIDTH}" height="{height}" rx="10"/></clipPath>
</defs>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono','Courier New',monospace;font-size:{FONT_SIZE}px;white-space:pre}}
.fg{{fill:{c['fg']}}}.dim{{fill:{c['dim']}}}.key{{fill:{c['key']}}}.accent{{fill:{c['accent']}}}.ok{{fill:{c['ok']}}}.num{{fill:{c['num']}}}.sh{{animation:sh 3s ease-in-out infinite}}@keyframes sh{{0%{{transform:translateX(0)}}60%,100%{{transform:translateX(1368px)}}}}@media (prefers-reduced-motion:reduce){{.sh{{animation:none;opacity:0}}}}
</style>
<g clip-path="url(#r)">
<rect width="{WIDTH}" height="{height}" fill="{c['bg']}"/>
<rect width="{WIDTH}" height="{BAR_H}" fill="{c['bar']}"/>
<circle cx="22" cy="{BAR_H/2}" r="6" fill="#ff5f56"/><circle cx="42" cy="{BAR_H/2}" r="6" fill="#ffbd2e"/><circle cx="62" cy="{BAR_H/2}" r="6" fill="#27c93f"/>
<text x="{WIDTH/2}" y="{BAR_H/2 + 5}" text-anchor="middle" class="dim">{escape(PROMPT_USER)}: ~</text>""")
    out.append(f'<g clip-path="url(#bt)"><rect x="0" y="{banner_y0 - 14}" width="{WIDTH}" height="{banner_h + 6}" fill="url(#bg)"/>'
               f'<rect class="sh" x="-299" y="{banner_y0 - 14}" width="257" height="{banner_h + 6}" fill="url(#bs)"/></g>')
    y = top
    last_len = 0
    for segs in lines:
        if segs:
            total = sum(len(t) for t, _ in segs)
            parts = "".join(f'<tspan class="{cl}">{escape(t)}</tspan>' for t, cl in segs)
            out.append(f'<text x="{PAD}" y="{y}" textLength="{total * CW:.1f}" lengthAdjust="spacing" xml:space="preserve">{parts}</text>')
            last_len = total
        y += LH
    cy = y - LH
    out.append(f'<rect x="{PAD + last_len * CW:.1f}" y="{cy - 13}" width="{CW:.1f}" height="17" fill="{c["fg"]}">'
               f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    out.append("</g></svg>")
    return "\n".join(out)


def main():
    if "--preview" in sys.argv:
        os.makedirs("previews", exist_ok=True)
        for name, (dark, light) in THEMES.items():
            open(f"previews/{name}-dark.svg", "w", encoding="utf-8").write(render(PLACEHOLDER, dark))
            open(f"previews/{name}-light.svg", "w", encoding="utf-8").write(render(PLACEHOLDER, light, light=True))
        print("previews written")
        return
    token = os.environ["ACCESS_TOKEN"]
    stats = fetch_stats(USER, token)
    open("dark_mode.svg", "w", encoding="utf-8").write(render(stats, THEMES[DARK_THEME][0]))
    open("light_mode.svg", "w", encoding="utf-8").write(render(stats, THEMES[LIGHT_THEME][1], light=True))
    print("updated", stats)


if __name__ == "__main__":
    main()
