"""Build the static pages of navidaftabi.github.io from data/*.json.

Run from the repository root:  python3 tools/build.py
GitHub Actions runs it on every push before deploying.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = "https://navidaftabi.github.io"
ME = "Navid Aftabi"
EMAIL = "aftabi@uw.edu"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

NAV = [
    ("Publications", "/publications/"),
    ("Teaching", "/teaching/"),
    ("Talks and Service", "/talks-and-service/"),
    ("CV", "/cv.pdf"),
]


def esc(s):
    return html.escape(s, quote=True)


def icon(paths, cls=""):
    body = "".join(f'<path d="{d}"/>' for d in paths)
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


ICONS = {
    "cv": ["M14 3v4a1 1 0 0 0 1 1h4", "M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2",
           "M11 12.5a1.5 1.5 0 0 0 -3 0v3a1.5 1.5 0 0 0 3 0", "M13 11l1.5 6l1.5 -6"],
    "scholar": ["M22 9l-10 -4l-10 4l10 4l10 -4v6", "M6 10.6v5.4a6 3 0 0 0 12 0v-5.4"],
    "orcid": ["M3 7a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v10a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3l0 -10",
              "M7 10a2 2 0 1 0 4 0a2 2 0 1 0 -4 0", "M15 8l2 0", "M15 12l2 0", "M7 16l10 0"],
    "github": ["M9 19c-4.3 1.4 -4.3 -2.5 -6 -3m12 5v-3.5c0 -1 .1 -1.4 -.5 -2c2.8 -.3 5.5 -1.4 5.5 -6a4.6 4.6 0 0 0 -1.3 -3.2a4.2 4.2 0 0 0 -.1 -3.2s-1.1 -.3 -3.5 1.3a12.3 12.3 0 0 0 -6.2 0c-2.4 -1.6 -3.5 -1.3 -3.5 -1.3a4.2 4.2 0 0 0 -.1 3.2a4.6 4.6 0 0 0 -1.3 3.2c0 4.6 2.7 5.7 5.5 6c-.6 .6 -.6 1.2 -.5 2v3.5"],
    "linkedin": ["M8 11v5", "M8 8v.01", "M12 16v-5", "M16 16v-3a2 2 0 1 0 -4 0",
                 "M3 7a4 4 0 0 1 4 -4h10a4 4 0 0 1 4 4v10a4 4 0 0 1 -4 4h-10a4 4 0 0 1 -4 -4l0 -10"],
    "mail": ["M3 7a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-10", "M3 7l9 6l9 -6"],
    "award": ["M6 9a6 6 0 1 0 12 0a6 6 0 1 0 -12 0", "M12 15l3.4 5.89l1.598 -3.233l3.598 .232l-3.4 -5.889",
              "M6.802 12l-3.4 5.89l3.598 -.233l1.598 3.232l3.4 -5.889"],
    "external": ["M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6", "M11 13l9 -9", "M15 4h5v5"],
}

PROFILE_LINKS = [
    ("CV", "/cv.pdf", "cv", True),
    ("Google Scholar", "https://scholar.google.com/citations?user=bAB22FwAAAAJ", "scholar", False),
    ("ORCID", "https://orcid.org/0000-0002-2063-1622", "orcid", False),
    ("GitHub", "https://github.com/navidaftabi", "github", False),
    ("LinkedIn", "https://www.linkedin.com/in/navid-aftabi", "linkedin", False),
    ("Email", f"mailto:{EMAIL}", "mail", False),
]

BIO = ("Navid Aftabi is a Ph.D. candidate in Industrial and Systems Engineering at the University of Washington, "
       "with a minor in Computer Science. His broader research interest spans systems modeling, optimization, and "
       "data science, with a focus on the cyber-physical security and resilience of industrial cyber-physical systems "
       "(ICPS). He develops data-driven and model-based methods integrating optimization, AI, and high-dimensional "
       "statistical learning methods for resilience assessment and design, system diagnosis and anomaly detection, and "
       "cyberattack-resilient control. His work appears in IISE Transactions, IEEE Transactions on Automation Science "
       "and Engineering, and the Journal of Manufacturing Systems. He holds M.Sc. degrees in Industrial Engineering "
       "from Sabanci University and in Industrial and Systems Engineering from Sharif University of Technology, and a "
       "B.Sc. in Computer Engineering from the University of Tabriz.")
DESCRIPTION = ("Navid Aftabi is a Ph.D. candidate in Industrial and Systems Engineering at the University of "
               "Washington, with a minor in Computer Science.")

JSON_LD = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": ME,
    "url": SITE + "/",
    "image": SITE + "/assets/img/navid-aftabi.jpg",
    "jobTitle": "Ph.D. Candidate",
    "affiliation": {"@type": "CollegeOrUniversity", "name": "University of Washington"},
    "alumniOf": [{"@type": "CollegeOrUniversity", "name": n} for n in
                 ("Sabanci University", "Sharif University of Technology", "University of Tabriz")],
    "email": f"mailto:{EMAIL}",
    "sameAs": [u for _, u, k, _ in PROFILE_LINKS if k in ("scholar", "orcid", "github", "linkedin")],
}


def page(path, title, body, current=None, description=DESCRIPTION, extra_head="", script=""):
    full_title = ME if title is None else f"{title} | {ME}"
    canonical = SITE + path
    cur = ' aria-current="page"'
    nav = "\n".join(
        f'      <a href="{href}"{cur if label == current else ""}>{label}</a>'
        for label, href in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="{ME}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="profile">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="Ph.D. Candidate, Industrial and Systems Engineering, University of Washington">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/img/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/source-serif-4-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
{extra_head}</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="/">{ME}</a>
    <nav class="nav" aria-label="Main">
{nav}
    </nav>
  </div>
</header>

<main id="main" class="wrap">
{body}
</main>

<footer class="site-footer">
  <div class="wrap">
    <span>&copy; 2026 {ME}</span>
    <a href="mailto:{EMAIL}">{EMAIL}</a>
  </div>
</footer>
{script}</body>
</html>
"""


def month(d):
    y, m = d.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def linked(text, link):
    """Wrap the {braced} part of text in a link; escape the rest."""
    m = re.search(r"\{(.+?)\}", text)
    if not m:
        return esc(text)
    a, b = text[:m.start()], text[m.end():]
    inner = esc(m.group(1))
    inner = f'<a href="{esc(link)}" rel="noopener">{inner}</a>' if link else inner
    return esc(a) + inner + esc(b)


def section(sid, heading, inner, sub=None):
    s = f'<span class="sub">{esc(sub)}</span>' if sub else ""
    return f"""  <section class="section" aria-labelledby="{sid}">
    <h2 id="{sid}">{esc(heading)}{s}</h2>
    <div>
{inner}
    </div>
  </section>"""


# ---------- home ----------
def build_home():
    news = json.loads((DATA / "news.json").read_text())
    rel = ' rel="noopener"'
    links = "\n".join(
        f'        <li><a class="btn{" btn-primary" if primary else ""}" href="{href}"'
        f'{rel if href.startswith("http") else ""}>{icon(ICONS[k])}{label}</a></li>'
        for label, href, k, primary in PROFILE_LINKS)
    items = "\n".join(
        f'      <li><time datetime="{n["date"]}">{month(n["date"])}</time><p>{linked(n["text"], n.get("link"))}</p></li>'
        for n in news)
    body = f"""  <section class="hero" aria-label="Introduction">
    <picture class="portrait">
      <source srcset="/assets/img/navid-aftabi.webp" type="image/webp">
      <img src="/assets/img/navid-aftabi.jpg" width="640" height="800" alt="Portrait of {ME}">
    </picture>
    <div>
      <p class="status">On the 2026-27 Academic Job Market</p>
      <h1>{ME}</h1>
      <p class="role">Ph.D. Candidate, Industrial and Systems Engineering<br>University of Washington</p>
      <ul class="links">
{links}
      </ul>
    </div>
  </section>

  <section class="section" aria-labelledby="about">
    <h2 id="about">About</h2>
    <p class="bio">{esc(BIO)}</p>
  </section>

  <section class="section" aria-labelledby="news">
    <h2 id="news">News</h2>
    <ul class="news">
{items}
    </ul>
  </section>"""
    ld = f'<script type="application/ld+json">\n{json.dumps(JSON_LD, indent=2)}\n</script>\n'
    return page("/", None, body, extra_head=ld)


# ---------- publications ----------
BIB_LAST = {"Omid Fatahi Valilai": ("Fatahi Valilai", "Omid"),
            "Niloufar Mirzavand Boroujeni": ("Mirzavand Boroujeni", "Niloufar")}


def split_name(n):
    if n in BIB_LAST:
        return BIB_LAST[n]
    first, last = n.rsplit(" ", 1)
    return last, first


def bibtex(p):
    if p.get("type") not in ("article", "preprint"):
        return None
    last0 = split_name(p["authors"][0])[0].split()[-1].lower()
    year = re.sub(r"\D", "", p["year"])[:4]
    words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in p["title"].split()]
    word = next((w for w in words if w and w not in ("a", "an", "the", "on", "of")), "paper")
    key = f"{last0}{year}{word}"
    authors = " and ".join("{}, {}".format(*split_name(a)) for a in p["authors"])
    authors = authors.replace("Fatahi Valilai,", "{Fatahi Valilai},").replace("Mirzavand Boroujeni,", "{Mirzavand Boroujeni},")
    tex = lambda s: s.replace("&", r"\&").replace("–", "--")
    if p["type"] == "article":
        f = [("author", authors), ("title", "{" + p["title"] + "}"), ("journal", tex(p["venue"])),
             ("year", year), ("volume", p.get("volume")), ("number", p.get("number")),
             ("pages", tex(p.get("pages", "")) or None), ("doi", p.get("doi"))]
        kind = "article"
    else:
        f = [("author", authors), ("title", "{" + p["title"] + "}"), ("year", year),
             ("eprint", p.get("arxiv")), ("archivePrefix", "arXiv"), ("doi", p.get("doi"))]
        kind = "misc"
    lines = ",\n".join(f"  {k} = {{{v}}}" for k, v in f if v)
    return f"@{kind}{{{key},\n{lines}\n}}"


def authors_html(names):
    return ", ".join(f"<strong>{esc(n)}</strong>" if n == ME else esc(n) for n in names)


def pub_item(p):
    url = f"https://doi.org/{p['doi']}" if p.get("doi") else None
    title = (f'<a href="{url}" rel="noopener">{esc(p["title"])}</a>' if url else esc(p["title"]))
    year = f" ({esc(p['year'])})" if p.get("year") else ""
    if p.get("type") == "article":
        parts = [f"Vol. {p['volume']}"] if p.get("volume") else []
        if p.get("number"):
            parts.append(f"Issue {p['number']}")
        if p.get("pages"):
            parts.append(f"pp. {p['pages']}")
        venue = f'<em>{esc(p["venue"])}</em>' + (", " + esc(", ".join(parts)) if parts else "")
    else:
        status = esc(p.get("status", ""))
        venue = f'{status} <em>{esc(p["venue"])}</em>' if p.get("venue") else status
    award = (f'\n          <p class="pub-award">{icon(ICONS["award"])}{esc(p["award"])}</p>'
             if p.get("award") else "")
    actions = []
    if url:
        actions.append(f'<a class="chip" href="{url}" rel="noopener">{esc(p.get("linkLabel", "DOI"))}</a>')
    bib = bibtex(p)
    if bib:
        actions.append(f'<details class="bib"><summary class="chip">BibTeX</summary>'
                       f'<pre>{esc(bib)}</pre><button class="chip copy" type="button">Copy</button></details>')
    act = f'\n          <div class="pub-actions">{"".join(actions)}</div>' if actions else ""
    lid = p["label"].replace(".", "")
    return f"""        <li class="entry pub" id="{lid}">
          <span class="pub-label">{esc(p['label'])}</span>
          <div>
          <h3 class="pub-title">{title}</h3>
          <p class="pub-meta">{authors_html(p['authors'])}{year}</p>
          <p class="pub-meta">{venue}</p>{award}{act}
          </div>
        </li>"""


COPY_JS = """<script>
document.querySelectorAll('.bib .copy').forEach(function (b) {
  b.addEventListener('click', function () {
    var t = b.parentElement.querySelector('pre').textContent;
    navigator.clipboard.writeText(t).then(function () {
      b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1500);
    });
  });
});
</script>
"""


def build_publications():
    d = json.loads((DATA / "publications.json").read_text())
    jump = "".join(f'<a class="chip" href="#{g["id"]}">{esc(g["title"])}</a>' for g in d["groups"])
    head = f"""  <header class="page-head">
    <h1>Publications</h1>
    <p class="page-note">{esc(d["legend"])}. <a href="https://scholar.google.com/citations?user=bAB22FwAAAAJ" rel="noopener">Google Scholar profile</a></p>
    <nav class="jump" aria-label="Sections">{jump}</nav>
  </header>"""
    secs = []
    for g in d["groups"]:
        items = "\n".join(pub_item(p) for p in g["items"])
        secs.append(section(g["id"], g["title"], f'      <ol class="entries">\n{items}\n      </ol>', g.get("subtitle")))
    return page("/publications/", "Publications", head + "\n\n" + "\n\n".join(secs), current="Publications",
                description="Publications of Navid Aftabi: journal papers, conference papers, submitted papers, working papers, and patents.",
                script=COPY_JS)


# ---------- teaching ----------
def build_teaching():
    d = json.loads((DATA / "teaching.json").read_text())
    ta = "\n".join(f"""        <li class="entry row">
          <div><h3 class="item-title">{esc(c['title'])}</h3>
          <p class="item-meta"><span class="code">{esc(c['code'])}</span> {esc(c['level'])}, {esc(c['institution'])}</p></div>
          <span class="when">{esc(c['terms'])}</span>
        </li>""" for c in d["assistant"])
    tr = "\n".join(f"""        <li class="entry row"><p class="item-plain">{esc(t['text'])}</p><span class="when">{esc(t['years'])}</span></li>"""
                   for t in d["training"])

    def mentor(m):
        link = (f' <a class="inline-ext" href="{esc(m["link"])}" rel="noopener" aria-label="Link for {esc(m["role"])}">'
                f'{icon(ICONS["external"])}</a>' if m.get("link") else "")
        return f"""        <li class="entry row">
          <div><h3 class="item-title">{esc(m['role'])}{link}</h3>
          <p class="item-meta">{esc(m['institution'])}</p></div>
          <span class="when">{esc(m['years'])}</span>
        </li>"""
    me = "\n".join(mentor(m) for m in d["mentoring"])
    head = """  <header class="page-head">
    <h1>Teaching</h1>
  </header>"""
    body = "\n\n".join([head,
                        section("assistant", "Teaching Assistant", f'      <ul class="entries">\n{ta}\n      </ul>'),
                        section("training", "Teaching Training", f'      <ul class="entries">\n{tr}\n      </ul>'),
                        section("mentoring", "Mentoring", f'      <ul class="entries">\n{me}\n      </ul>')])
    return page("/teaching/", "Teaching", body, current="Teaching",
                description="Teaching, teaching training, and mentoring experience of Navid Aftabi.")


# ---------- talks and service ----------
def build_talks_service():
    d = json.loads((DATA / "talks_service.json").read_text())
    talks = "\n".join(f"""        <li class="entry dated"><span class="when">{esc(t['year'])}</span>
          <div><h3 class="item-title">{esc(t['title'])}</h3>
          <p class="item-meta">{esc(t['venue'])}, {esc(t['place'])}</p></div>
        </li>""" for t in d["talks"])

    def simple(xs):
        return "\n".join(f'        <li class="entry"><p class="item-plain">{esc(x)}</p></li>' for x in xs)

    def cols(xs):
        return "\n".join(f"        <li>{esc(x)}</li>" for x in xs)
    service = f"""      <h3 class="group">Track Chair</h3>
      <ul class="entries">
{simple(d['track_chair'])}
      </ul>
      <h3 class="group">Session Chair</h3>
      <ul class="entries">
{simple(d['session_chair'])}
      </ul>
      <h3 class="group">Journal Referee</h3>
      <ul class="cols">
{cols(d['journal_referee'])}
      </ul>
      <h3 class="group">Conference Referee</h3>
      <ul class="cols">
{cols(d['conference_referee'])}
      </ul>"""
    mem = "\n".join(f'        <li class="entry row"><p class="item-plain">{esc(m["name"])}</p><span class="when">{esc(m["years"])}</span></li>'
                    for m in d["memberships"])
    head = """  <header class="page-head">
    <h1>Talks and Service</h1>
  </header>"""
    body = "\n\n".join([head,
                        section("talks", "Selected Presentations", f'      <ul class="entries">\n{talks}\n      </ul>'),
                        section("service", "Professional Service", service),
                        section("memberships", "Professional Memberships", f'      <ul class="entries">\n{mem}\n      </ul>')])
    return page("/talks-and-service/", "Talks and Service", body, current="Talks and Service",
                description="Selected presentations, professional service, and memberships of Navid Aftabi.")


def build_404():
    body = """  <header class="page-head">
    <h1>Page not found</h1>
    <p class="page-note">This page does not exist. <a href="/">Go to the home page</a>.</p>
  </header>"""
    return page("/404.html", "Page not found", body)


def main():
    out = {
        "index.html": build_home(),
        "publications/index.html": build_publications(),
        "teaching/index.html": build_teaching(),
        "talks-and-service/index.html": build_talks_service(),
        "404.html": build_404(),
    }
    for rel, text in out.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print("wrote", rel)


if __name__ == "__main__":
    main()
