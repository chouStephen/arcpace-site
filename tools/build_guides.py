#!/usr/bin/env python3
"""
Builds the guide pages. The clothing table and WBGT examples come from
tools/guide-data.json, a cut of the ArcPace app's model output holding only
what the pages show (the pace model stays private: never publish it):

    cd ../runcast && npx tsx scripts/site-tables.ts | jq '{wear, wbgt}' > ../arcpace-site/tools/guide-data.json
    cd ../arcpace-site && python3 tools/build_guides.py

Also writes sitemap.xml, since the guide list lives here.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://arcpace.app"
UPDATED = "2026-10-14"
# Flip with the home page's APP_LIVE once Apple approves the app: guide
# calls to action then go straight to the App Store.
APP_LIVE = True
APP_STORE_ID = "6815307156"
APP_STORE_URL = f"https://apps.apple.com/app/id{APP_STORE_ID}"
D = json.loads((ROOT / "tools/guide-data.json").read_text())

esc = html.escape


def pace(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def signed(sec):
    if sec == 0:
        return "0"
    return f"+{sec}" if sec > 0 else f"−{-sec}"


STYLE = """
  :root { --bg:#FBFBFD; --ink:#1B1F2A; --dim:#5A6070; --faint:#8A90A0; --rule:#E6E8EE; --accent:#0E8A5C; --cell:#F1F3F7; }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) { --bg:#07090F; --ink:#F4F6FB; --dim:rgba(244,246,251,0.72); --faint:rgba(244,246,251,0.42); --rule:rgba(255,255,255,0.10); --accent:#3DDC97; --cell:rgba(255,255,255,0.05); color-scheme:dark; }
  }
  :root[data-theme="dark"] { --bg:#07090F; --ink:#F4F6FB; --dim:rgba(244,246,251,0.72); --faint:rgba(244,246,251,0.42); --rule:rgba(255,255,255,0.10); --accent:#3DDC97; --cell:rgba(255,255,255,0.05); color-scheme:dark; }
  :root[data-theme="light"] { color-scheme:light; }
  html { background:var(--bg); color:var(--ink); }
  body { margin:0; padding:0; font:16px/1.6 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif; -webkit-font-smoothing:antialiased; }
  main { max-width:720px; margin:0 auto; padding:32px 16px 80px; }
  h1 { font-size:30px; line-height:1.2; letter-spacing:-0.01em; margin:0 0 8px; }
  h2 { font-size:21px; margin:44px 0 8px; }
  p, li { color:var(--dim); margin:0 0 12px; }
  ul, ol { padding-left:20px; margin:0 0 12px; }
  a { color:var(--accent); text-decoration:none; }
  a:hover { text-decoration:underline; }
  strong { color:var(--ink); }
  .lede { font-size:18px; color:var(--ink); }
  .meta { color:var(--faint); font-size:13px; margin-bottom:20px; }
  .answer { background:var(--cell); border-radius:14px; padding:16px 18px; margin:20px 0; }
  .answer p { color:var(--ink); margin:0; }
  .scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; margin:12px 0 8px; }
  table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; font-size:15px; }
  caption { text-align:left; color:var(--faint); font-size:13px; padding-bottom:8px; caption-side:top; }
  th, td { padding:8px 8px; border-bottom:1px solid var(--rule); text-align:right; white-space:nowrap; }
  th:first-child, td:first-child { text-align:left; }
  td.wrap, th.wrap { white-space:normal; text-align:left; }
  thead th { color:var(--faint); font-weight:600; font-size:13px; }
  .note { color:var(--faint); font-size:13px; }
  h2 .anchor { color:var(--faint); font-weight:400; opacity:0; text-decoration:none; }
  h2:hover .anchor, h2 .anchor:focus { opacity:1; }
  @media (hover:none) { h2 .anchor { display:none; } }
  .related li { margin-bottom:8px; }
  @media (max-width:430px) { table { font-size:14px; } th, td { padding:7px 5px; } thead th { font-size:12px; } }
  details { border-bottom:1px solid var(--rule); padding:12px 0; }
  summary { cursor:pointer; color:var(--ink); font-weight:600; }
  details p { margin-top:8px; }
  .cta { margin:44px 0 0; padding:20px; border-radius:16px; background:var(--cell); }
  .cta p { margin:0; color:var(--ink); }
  footer a { padding:6px 0; }
  footer { margin-top:56px; padding-top:16px; border-top:1px solid var(--rule); color:var(--faint); font-size:13px; display:flex; gap:14px; flex-wrap:wrap; }
"""


PENDING = []


def page(path, title, description, h1, body, faq, crumb, sources=None, meta_line="Figures from the ArcPace weather model"):
    """Queue a page. Pages are written last, once every page's title is known for the related links."""
    PENDING.append(dict(path=path, title=title, description=description, h1=h1, body=body, faq=faq,
                        crumb=crumb, sources=sources, meta_line=meta_line))
    return path


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", text)).lower()).strip("-")


def anchors(markup):
    """Every h2 gets an id and a # link, so a link (or an AI answer) can point at one section."""
    def one(m):
        sid = slug(m.group(1))
        return f'<h2 id="{sid}">{m.group(1)} <a class="anchor" href="#{sid}" aria-label="Link to this section">#</a></h2>'
    return re.sub(r"<h2>(.*?)</h2>", one, markup)


def render(path, title, description, h1, body, faq, crumb, sources, meta_line, related_html=""):
    """One guide page: its own title and description, Article, FAQPage and BreadcrumbList data."""
    url = f"{SITE}/{path}"
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": h1,
            "description": description,
            "url": url,
            "datePublished": UPDATED,
            "dateModified": UPDATED,
            "author": {"@type": "Organization", "name": "ArcPace", "url": SITE + "/"},
            "publisher": {"@type": "Organization", "name": "ArcPace", "url": SITE + "/",
                          "logo": {"@type": "ImageObject", "url": SITE + "/img/icon.png"}},
            "image": SITE + "/img/og-v4.png",
            "isPartOf": {"@type": "WebSite", "name": "ArcPace", "url": SITE + "/"},
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ArcPace", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides/"},
                {"@type": "ListItem", "position": 3, "name": crumb, "item": url},
            ],
        },
    ]
    if faq:
        ld.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq],
        })
    faq_html = ""
    if faq:
        faq_html = "<h2>Questions</h2>\n" + "\n".join(
            f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
    if sources:
        faq_html += "\n<h2>Sources</h2>\n<ul>" + "".join(
            f"<li><a href='{esc(u)}' rel='noopener'>{esc(n)}</a></li>" for n, u in sources) + "</ul>"
        ld[0]["citation"] = [u for _, u in sources]
    ld_html = "\n".join(
        f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/img/og-v4.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/img/favicon.png">
<meta name="apple-itunes-app" content="app-id={APP_STORE_ID}, app-argument={url}">
<link rel="stylesheet" href="/site-bar.css">
<style>{STYLE}</style>
<script>
  // A saved Light/Dark choice from the home page, before first paint.
  try {{ var t = localStorage.getItem('arcpace-theme'); if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; }} catch (e) {{}}
</script>
{ld_html}
</head>
<body>
<nav class="topbar" aria-label="Site"><div class="topbar-inner"><a class="brand" href="/" aria-label="ArcPace home"><img src="/img/icon.png" width="28" height="28" alt=""><span class="brand-name">ArcPace</span></a><div class="topnav"><a href="/calculator/">Calculator</a><a href="/guides/" aria-current="page">Guides</a></div><div class="theme" role="group" aria-label="Appearance">
  <button type="button" data-theme-choice="auto" aria-label="Automatic, follows your device" title="Auto">
    <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10 3a7 7 0 0 1 0 14z" fill="currentColor"/></svg>
  </button>
  <button type="button" data-theme-choice="light" aria-label="Light" title="Light">
    <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.6" fill="currentColor"/><g stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M10 1.8v2.2M10 16v2.2M1.8 10H4M16 10h2.2M4.2 4.2l1.6 1.6M14.2 14.2l1.6 1.6M4.2 15.8l1.6-1.6M14.2 5.8l1.6-1.6"/></g></svg>
  </button>
  <button type="button" data-theme-choice="dark" aria-label="Dark" title="Dark">
    <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16.5 12.6A7 7 0 0 1 7.4 3.5a7 7 0 1 0 9.1 9.1z" fill="currentColor"/></svg>
  </button>
    </div></div></nav>
<main>
<h1>{esc(h1)}</h1>
<p class="meta">Updated {UPDATED} · {meta_line}</p>
{anchors(body)}
{anchors(faq_html)}
{related_html}
<div class="cta"><p><strong>ArcPace</strong> scores every hour of your forecast 0–100, with the pace cost at your easy pace and what to wear. Free for iPhone. {'<a href="' + APP_STORE_URL + '">Get it on the App Store</a>' if APP_LIVE else '<a href="/">See the app</a>'}</p></div>
<footer><a href="/">Home</a><a href="/calculator/">Calculator</a><a href="/guides/">Guides</a><a href="/support/">Support</a><a href="/privacy/">Privacy</a></footer>
</main>
<script src="/theme.js"></script>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "8eb1d101134840ad957fc4443d5d909c"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
"""
    dest = ROOT / path / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return path


# ---------------------------------------------------------------- pace ----
# This page explains what drives the pace cost, in words and rounded ranges.
# It deliberately publishes no formula, baseline or table from the model:
# the model stays private so it can change, and so it can't be copied.
pace_body = """
<div class="answer"><p><strong>Short answer:</strong> on a muggy summer morning, expect to lose somewhere between
<strong>15 and 60 seconds per mile</strong> at the same effort, and more in full sun or real heat.
Dew point matters as much as temperature, sun adds more on top, and slower runners lose more than fast ones.
A cool, dry morning works the other way: you run a few seconds per mile faster for the same effort.</p></div>

<p class="lede">Your body sheds the heat of running mostly by sweating, and sweat cools you only when it evaporates.
Anything that slows evaporation, or adds heat, leaves less of your effort for speed.</p>

<h2>What drives the cost</h2>
<ul>
<li><strong>Dew point.</strong> The amount of water already in the air. Humid air takes up sweat slowly, so it drips instead of cooling you.
It's the biggest single factor most runners underrate.</li>
<li><strong>Air temperature.</strong> The warmer the air, the less heat your skin can lose to it. On its own, warm dry air costs far less than the same temperature when it's humid.</li>
<li><strong>Sun.</strong> Direct sun is a heat load the thermometer misses. The same hour costs more at midday in full sun than under cloud, in shade or at dawn.</li>
<li><strong>Wind.</strong> In the heat, a breeze helps you cool; still, heavy air makes it worse. In the cold, wind turns a mild day raw. Running into a headwind also costs effort directly.</li>
<li><strong>Your pace.</strong> Slower runners lose more, in seconds and as a share of their pace. They're out longer and make less cooling airflow.</li>
<li><strong>Your heat tolerance.</strong> Some runners handle heat better, and everyone gets better after 10–14 days of training in it.</li>
<li><strong>Rain, snow and altitude</strong> add their own costs: wet or icy footing, cold rain, and thinner air at elevation.</li>
</ul>

<h2>Dew point: the number to check</h2>
<p>Relative humidity depends on the temperature, so 90% at dawn can feel fine and 50% in the afternoon miserable.
Dew point measures the water in the air directly, so it tells you more about a run:</p>
<ul>
<li><strong>Under about 55°F:</strong> comfortable. Heat costs little unless the air itself is hot.</li>
<li><strong>55–65°F:</strong> noticeable. A warm morning starts to cost real time.</li>
<li><strong>65–70°F:</strong> sticky. Easy runs feel hard; slow down by effort.</li>
<li><strong>Over 70°F:</strong> oppressive. Expect a big slowdown, and take the <a href="/guides/heat-illness-warning-signs/">heat illness warning signs</a> seriously.</li>
</ul>

<h2>What it adds up to</h2>
<p>Rough ranges, in shade, for easy paces from about 8:00 to 12:00 per mile; the faster runner is at the low end:</p>
<ul>
<li><strong>Cool and dry</strong> (about 50°F, dew point 35°F): a few seconds per mile <em>faster</em>.</li>
<li><strong>Mild</strong> (about 65°F, dew point 55°F): close to no change.</li>
<li><strong>Warm and humid</strong> (about 75°F, dew point 65°F): roughly 15–40 seconds per mile slower.</li>
<li><strong>Muggy</strong> (about 80°F, dew point 70°F): roughly 25–60 seconds per mile slower.</li>
<li><strong>Hot and steamy</strong> (about 85°F, dew point 75°F): roughly 30–85 seconds per mile slower, and more as it gets hotter.</li>
</ul>
<p>Full sun adds more on top of each of these. These are planning ranges, not a prediction for your run: ArcPace works out
the number for your pace, your heat tolerance and each hour's actual forecast.</p>

<h2>Why slower runners lose more</h2>
<p>Most heat charts come from competitive race results. But in marathon data (Ely and colleagues, 2007),
the leaders lost under 1% for each 5°C of heat stress while runners further back lost over 3%.
Slower runners spend longer in the heat and make less cooling airflow, so a fixed adjustment undercounts the cost for them.</p>

<p class="note">Estimates for planning easy runs, not medical advice. In real heat, slow down by feel, drink, and stop if you feel unwell.
For race-day risk, see <a href="/guides/wbgt-running-heat-flags/">WBGT and heat flags</a>; for how to stay cool, <a href="/guides/running-in-the-heat/">how to run in the heat</a>.</p>
"""
pace_faq = [
    ("How much slower should I run in heat and humidity?",
     "On a muggy summer morning, roughly 15 to 60 seconds per mile at the same effort, more in full sun or real heat. Dew point matters as much as temperature, and slower runners lose more than fast ones."),
    ("Is dew point or humidity better for running?",
     "Dew point. Relative humidity depends on the temperature, so 90% at dawn can be comfortable and 50% in the afternoon miserable. Dew point measures the water in the air directly: under about 55°F feels fine, 55–65°F is noticeable, and over 70°F is oppressive."),
    ("How much does 80 degrees slow running?",
     "It depends on the dew point, the sun and your pace. At 80°F with a muggy 70°F dew point, in shade, easy runners typically lose roughly 25 to 60 seconds per mile; with dry air, far less."),
    ("Does running in the sun make a difference?",
     "Yes. Direct sun adds a heat load the air temperature doesn't show, so the same hour costs more at midday in full sun than under cloud or at dawn."),
    ("Do you run faster in cool weather?",
     "A little. A cool, dry morning lets you run a few seconds per mile faster for the same effort than a mild day."),
]

# ---------------------------------------------------------------- wear ----
groups = []
for w in D["wear"]:
    items = [i["label"] for i in w["items"]]
    if groups and groups[-1]["items"] == items:
        groups[-1]["to"] = w["tempF"]
    else:
        groups.append({"from": w["tempF"], "to": w["tempF"], "items": items})


def span(g, last):
    if last:
        return f"{g['from']}°F and up"
    return f"{g['from']}°F" if g["from"] == g["to"] else f"{g['from']}–{g['to']}°F"


wear_rows = "".join(
    f"<tr><td><strong>{span(g, k == len(groups) - 1)}</strong></td><td class='wrap'>{esc(', '.join(g['items']))}</td></tr>"
    for k, g in enumerate(groups))
tee = next(g for g in groups if "Technical tee" in g["items"])
singlet = next(g for g in groups if any("Singlet" in x for x in g["items"]))
tights = [g for g in groups if any("ights" in x for x in g["items"])]
wear_body = f"""
<div class="answer"><p><strong>Short answer:</strong> dress for about 15–20°F warmer than it is, because you warm up within the
first mile. In dry weather with light wind: a technical tee and shorts from about {tee['from']}°F to {tee['to']}°F,
a singlet from about {singlet['from']}°F, and tights below about {tights[-1]['to'] + 5}°F.
You should feel slightly cold at the door.</p></div>

<h2>What to wear, by temperature</h2>
<div class='scroll'><table><caption>Daytime, dry, light wind (5 mph), default cold and heat tolerance. Temperature is what it feels like outside.</caption>
<thead><tr><th>Temperature</th><th class='wrap'>Wear</th></tr></thead><tbody>{wear_rows}</tbody></table></div>

<h2>What changes the answer</h2>
<ul>
<li><strong>Wind</strong> strips heat fast. In the cold, a windproof layer matters more than a thicker one. <a href="/guides/running-in-the-cold/">Running in the cold</a>.</li>
<li><strong>Rain</strong> near freezing is the coldest running there is: add a shell and gloves even when the number looks mild. <a href="/guides/rain-wind-storms-air-quality/">Running in rain and wind</a>.</li>
<li><strong>Sun and humidity</strong> push the warm side up: light colors, a cap and sunglasses, and plan water.</li>
<li><strong>You.</strong> Some runners run hot, some cold. ArcPace lets you set your cold and heat tolerance, and shifts the kit to match.</li>
<li><strong>Long runs</strong> start cold and finish warm. Pick layers you can take off and carry.</li>
</ul>
<p>ArcPace applies this to every forecast hour, dressing you for mile two from the feels-like temperature, wind, rain and sun.</p>
"""
wear_faq = [
    ("What should I wear running in 40 degrees?",
     "In dry weather with light wind: a light long sleeve, shorts or capris, light gloves and a headband over the ears. Add a windproof layer if it's breezy or wet."),
    ("What should I wear running in 30 degrees?",
     "A long sleeve with a light vest, tights, light gloves and a beanie over the ears, in dry weather with light wind."),
    ("Should I wear shorts or tights?",
     f"Shorts down to about 40°F for most runners in dry weather; tights below that. Legs warm up fast; hands and ears don't."),
    ("Why should I feel cold when I start a run?",
     "Running produces a lot of heat. Within the first mile you'll feel about 15–20°F warmer than standing still, so if you're comfortable at the door you'll be too hot by mile two."),
]

# ---------------------------------------------------------------- wbgt ----
FLAGS = [
    ("Black", "82°F and up", "28°C and up", "Extreme risk. Races are typically cancelled. Don't race or do hard training."),
    ("Red", "73–82°F", "23–28°C", "High risk. Slow down a lot, drink, and consider not racing if you're not adapted to heat."),
    ("Yellow", "64–73°F", "18–23°C", "Moderate risk. Slow down, drink, and watch for heat illness."),
    ("Green", "50–64°F", "10–18°C", "Low risk of heat illness. Normal running."),
    ("White", "below 50°F", "below 10°C", "Low heat risk. The risk now is cold: hypothermia in wet, windy conditions."),
]
flag_rows = "".join(f"<tr><td><strong>{f}</strong></td><td>{fr}</td><td>{cr}</td><td class='wrap'>{esc(m)}</td></tr>" for f, fr, cr, m in FLAGS)
ex_rows = "".join(
    f"<tr><td>{w['tempF']}°F</td><td>{w['dewpointF']}°F</td><td>{'shade' if w['solarWm2'] == 0 else str(w['solarWm2']) + ' W/m²'}</td>"
    f"<td>{w['wbgtF']}°F</td><td>{w['flag']}</td></tr>" for w in D["wbgt"])
wbgt_body = f"""
<div class="answer"><p><strong>Short answer:</strong> WBGT (wet bulb globe temperature) is the heat-stress reading race directors use.
It combines air temperature, humidity, sun and wind. Races fly a flag by it: <strong>Green</strong> below 64°F WBGT,
<strong>Yellow</strong> 64–73°F, <strong>Red</strong> 73–82°F and <strong>Black</strong> at 82°F and up, when races are usually cancelled.</p></div>

<p class="lede">75°F in dry shade is pleasant; 75°F in full sun with a 70°F dew point is dangerous. WBGT captures the difference:
it weighs humidity most, then sun, then air temperature.</p>

<h2>The race heat flags</h2>
<div class='scroll'><table><caption>WBGT flag ranges as used at races (after the American College of Sports Medicine guidance).</caption>
<thead><tr><th>Flag</th><th>WBGT °F</th><th>WBGT °C</th><th class='wrap'>What it means</th></tr></thead><tbody>{flag_rows}</tbody></table></div>

<h2>Examples</h2>
<div class='scroll'><table><caption>WBGT estimated by the ArcPace model, 5 mph wind.</caption>
<thead><tr><th>Air</th><th>Dew point</th><th>Sun</th><th>WBGT</th><th>Flag</th></tr></thead><tbody>{ex_rows}</tbody></table></div>
<p>WBGT is usually lower than the air temperature, so a WBGT of 80°F is a very hot day, not a warm one.</p>

<h2>How ArcPace uses it</h2>
<p>ArcPace estimates WBGT for every hour of the forecast from temperature, dew point, solar radiation and wind, and shows the flag
beside the run score, described in plain words. The flag is shown, not scored: the run score already counts heat and humidity,
and the flag is there for race-day decisions.</p>
<p class="note">Estimates from forecast data, not a measured reading. On race day, follow the organizer's official flag.
Not medical advice. Know the <a href="/guides/heat-illness-warning-signs/">heat illness warning signs</a>.</p>
"""
wbgt_faq = [
    ("What is WBGT in running?",
     "Wet bulb globe temperature: a heat-stress measure that combines air temperature, humidity, sun and wind. Races use it to set heat flags."),
    ("What WBGT is too hot to run?",
     "At a WBGT of 82°F (28°C) or more, the Black flag, races are typically cancelled. 73–82°F (Red) is high risk: slow down a lot and consider not racing."),
    ("Is WBGT the same as the heat index?",
     "No. The heat index combines temperature and humidity for a person in shade. WBGT also counts sun and wind, which is why it's used for exercise and races."),
    ("Why is WBGT lower than the temperature?",
     "WBGT weights the wet bulb reading, which is cooled by evaporation, most heavily. So its numbers run lower than the air temperature, and the flag thresholds are set to match."),
]

# ---------------------------------------------------------------- build ----
GUIDES = [
    (page("guides/running-pace-heat-humidity/",
          "How much do heat and humidity slow your running pace? | ArcPace",
          "A muggy morning can cost 15–60 seconds per mile. What drives it: dew point, temperature, sun, wind and your own pace, and why slower runners lose more.",
          "How much do heat and humidity slow your running pace?", pace_body, pace_faq, "Heat, humidity and pace",
          meta_line="General guidance, not medical advice"),
     "How much do heat and humidity slow your running pace?",
     "What drives the slowdown, why dew point matters, and why slower runners lose more."),
    (page("guides/what-to-wear-running-by-temperature/",
          "What to wear running, by temperature | ArcPace",
          "What to wear for a run at every temperature from 10°F to 90°F, and how wind, rain and sun change it. Dress for 15–20°F warmer than it is.",
          "What to wear running, by temperature", wear_body, wear_faq, "What to wear running"),
     "What to wear running, by temperature",
     "From 10°F to 90°F, and how wind, rain and sun change it."),
    (page("guides/wbgt-running-heat-flags/",
          "WBGT and race heat flags, explained for runners | ArcPace",
          "WBGT is the heat-stress reading races use. Green below 64°F, Yellow 64–73°F, Red 73–82°F, Black 82°F and up. What each flag means for your run.",
          "WBGT and race heat flags, explained for runners", wbgt_body, wbgt_faq, "WBGT and heat flags"),
     "WBGT and race heat flags, explained",
     "What wet bulb globe temperature measures, and what each race flag means."),
]

# ------------------------------------------------------------ articles ----
import re
VALUES = {}
ARTICLES = []
for f in sorted((ROOT / "content").glob("*.html")):
    raw = f.read_text()
    m = re.match(r"<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    meta = json.loads(m.group(1))
    body = raw[m.end():]
    for k, v in VALUES.items():
        body = body.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{(\w+)\}\}", body)
    if left:
        raise SystemExit(f"{f.name}: no value for {left}")
    path = f"guides/{meta['slug']}/"
    page(path, meta["title"], meta["description"], meta["h1"], body, meta["faq"], meta["crumb"],
         meta.get("sources"), "General guidance, not medical advice")
    ARTICLES.append((path, meta["listTitle"], meta["listBlurb"]))
ORDER = ["running-in-the-heat", "heat-illness-warning-signs", "running-in-the-cold", "rain-wind-storms-air-quality"]
ARTICLES.sort(key=lambda a: ORDER.index(a[0].split("/")[1]) if a[0].split("/")[1] in ORDER else 99)

art_items = "".join(f"<li><a href='/{p}'><strong>{esc(t)}</strong></a><br>{esc(d)}</li>" for p, t, d in ARTICLES)
hub_items = "".join(f"<li><a href='/{p}'><strong>{esc(t)}</strong></a><br>{esc(d)}</li>" for p, t, d in GUIDES)
page("guides/", "Running weather guides | ArcPace",
     "Guides to running in the weather: staying cool in the heat, heat illness warning signs, cold, rain, wind, storms and smoke, plus pace, clothing and WBGT heat flags.",
     "Running weather guides",
     f"<p class='lede'>How the weather changes a run: practical guides, and what drives your pace in the heat.</p>"
     f"<p>For a number: the <a href='/calculator/'><strong>running weather calculator</strong></a> gives a run score, pace cost and what to wear for any weather and your pace.</p>"
     f"<h2>Running in the weather</h2><ul>{art_items}</ul><h2>Pace, clothing and heat flags</h2><ul>{hub_items}</ul>",
     None, "Guides")

RELATED = {
    "running-in-the-heat": ["heat-illness-warning-signs", "running-pace-heat-humidity", "wbgt-running-heat-flags"],
    "heat-illness-warning-signs": ["running-in-the-heat", "wbgt-running-heat-flags", "running-pace-heat-humidity"],
    "running-in-the-cold": ["what-to-wear-running-by-temperature", "rain-wind-storms-air-quality", "running-in-the-heat"],
    "rain-wind-storms-air-quality": ["running-in-the-cold", "running-in-the-heat", "what-to-wear-running-by-temperature"],
    "running-pace-heat-humidity": ["running-in-the-heat", "wbgt-running-heat-flags", "heat-illness-warning-signs"],
    "what-to-wear-running-by-temperature": ["running-in-the-cold", "running-in-the-heat", "rain-wind-storms-air-quality"],
    "wbgt-running-heat-flags": ["heat-illness-warning-signs", "running-in-the-heat", "running-pace-heat-humidity"],
}
TITLES = {p.split("/")[1]: (p, t, d) for p, t, d in ARTICLES + GUIDES}
for spec in PENDING:
    key = spec["path"].split("/")[1] if spec["path"].count("/") > 1 else ""
    rel = RELATED.get(key, [])
    related_html = ""
    if rel:
        related_html = "<h2>Related guides</h2><ul class='related'>" + "".join(
            f"<li><a href='/{TITLES[r][0]}'>{esc(TITLES[r][1])}</a><br><span class='note'>{esc(TITLES[r][2])}</span></li>" for r in rel) + "</ul>"
    render(related_html=related_html, **spec)

urls = ["", "calculator/", "guides/"] + [p for p, _, _ in ARTICLES] + [p for p, _, _ in GUIDES] + ["support/", "privacy/"]
sitemap = "\n".join(f"  <url><loc>{SITE}/{u}</loc><lastmod>{UPDATED}</lastmod></url>" for u in urls)
(ROOT / "sitemap.xml").write_text(
    f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}\n</urlset>\n')
print("built", len(GUIDES) + len(ARTICLES) + 1, "pages and sitemap.xml")
