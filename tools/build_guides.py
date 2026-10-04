#!/usr/bin/env python3
"""
Builds the guide pages from guides/data.json, which comes from the ArcPace
app's own model:

    cd ../runcast && npx tsx scripts/site-tables.ts > ../arcpace-site/guides/data.json
    cd ../arcpace-site && python3 tools/build_guides.py

Every number on a guide page is read from that file, never typed, so the
site cannot quote a pace cost the app would not give. Also writes
sitemap.xml, since the guide list lives here.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://arcpace.app"
UPDATED = "2026-10-04"
D = json.loads((ROOT / "guides/data.json").read_text())

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
    :root { --bg:#07090F; --ink:#F4F6FB; --dim:rgba(244,246,251,0.72); --faint:rgba(244,246,251,0.42); --rule:rgba(255,255,255,0.10); --accent:#3DDC97; --cell:rgba(255,255,255,0.05); }
  }
  html { background:var(--bg); color:var(--ink); }
  body { margin:0; padding:40px 16px 80px; font:16px/1.6 -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif; -webkit-font-smoothing:antialiased; }
  main { max-width:720px; margin:0 auto; }
  h1 { font-size:30px; line-height:1.2; letter-spacing:-0.01em; margin:0 0 8px; }
  h2 { font-size:21px; margin:44px 0 8px; }
  p, li { color:var(--dim); margin:0 0 12px; }
  ul, ol { padding-left:20px; margin:0 0 12px; }
  a { color:var(--accent); text-decoration:none; }
  a:hover { text-decoration:underline; }
  strong { color:var(--ink); }
  .lede { font-size:18px; color:var(--ink); }
  .meta { color:var(--faint); font-size:13px; margin-bottom:20px; }
  nav.crumbs { font-size:14px; padding:12px 0; margin-bottom:20px; border-bottom:1px solid var(--rule); display:flex; gap:14px; flex-wrap:wrap; }
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
  @media (max-width:430px) { table { font-size:14px; } th, td { padding:7px 5px; } thead th { font-size:12px; } }
  details { border-bottom:1px solid var(--rule); padding:12px 0; }
  summary { cursor:pointer; color:var(--ink); font-weight:600; }
  details p { margin-top:8px; }
  .cta { margin:44px 0 0; padding:20px; border-radius:16px; background:var(--cell); }
  .cta p { margin:0; color:var(--ink); }
  footer { margin-top:56px; padding-top:16px; border-top:1px solid var(--rule); color:var(--faint); font-size:13px; display:flex; gap:14px; flex-wrap:wrap; }
"""


def page(path, title, description, h1, body, faq, crumb, sources=None, meta_line="Figures from the ArcPace weather model"):
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
            "image": SITE + "/img/og.png",
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
<meta property="og:image" content="{SITE}/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/img/favicon.png">
<style>{STYLE}</style>
{ld_html}
</head>
<body>
<main>
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">ArcPace</a><a href="/guides/">Guides</a></nav>
<h1>{esc(h1)}</h1>
<p class="meta">Updated {UPDATED} · {meta_line}</p>
{body}
{faq_html}
<div class="cta"><p><strong>ArcPace</strong> does this for every hour of your forecast: a run score out of 100, the pace cost at your own easy pace, and what to wear. Free for iPhone. <a href="/">See the app</a></p></div>
<footer><a href="/">Home</a><a href="/guides/">Guides</a><a href="/support/">Support</a><a href="/privacy/">Privacy</a></footer>
</main>
</body>
</html>
"""
    dest = ROOT / path / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return path


# ---------------------------------------------------------------- pace ----
paces = D["paces"]
by_sum = D["bySum"]
ex = D["examples"]
row = {r["sum"]: r for r in by_sum}
i10 = paces.index(600)


def sum_table(kind, caption):
    head = "".join(f"<th>{pace(p)} pace</th>" for p in paces)
    rows = "".join(
        f"<tr><td><strong>{r['sum']}</strong><br><span class='note'>e.g. {esc(r['example'].replace('°F / dew point ', '° / dp '))}</span></td>"
        + "".join(f"<td>{signed(v)}</td>" for v in r[kind]) + "</tr>"
        for r in by_sum)
    return (f"<div class='scroll'><table><caption>{esc(caption)} Column heads are easy pace per mile.</caption>"
            f"<thead><tr><th>Temp + dew point</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>")


def grid_table():
    t10 = next(t for t in D["paceTables"] if t["paceSecPerMile"] == 600)["shade"]
    head = "".join(f"<th>{d}°</th>" for d in D["dews"])
    body = "".join(
        f"<tr><td><strong>{t}°F</strong></td>" + "".join(
            f"<td>{'' if v is None else signed(v)}</td>" for v in vals) + "</tr>"
        for t, vals in zip(D["temps"], t10))
    return (f"<div class='scroll'><table><caption>Seconds per mile added at a 10:00/mile easy pace, in shade. "
            f"Rows: air temperature. Columns: dew point.</caption>"
            f"<thead><tr><th>Temp \\ dew point</th>{head}</tr></thead><tbody>{body}</tbody></table></div>")


s140, s150, s160 = row[140]["shade"][i10], row[150]["shade"][i10], row[160]["shade"][i10]
fs = ex["fast_vs_slow_80_65_shade"]
pace_body = f"""
<div class="answer"><p><strong>Short answer:</strong> add the air temperature and the dew point in °F.
Below about 120 the weather costs nothing, and a cool, dry day even helps; at 120 it's a few seconds. Above that, the cost climbs fast: at a 10:00/mile easy pace,
a sum of 140 adds about <strong>{s140} seconds per mile</strong>, 150 adds about <strong>{s150}</strong>, and 160 about <strong>{s160}</strong>.
Slower runners lose more: on an 80°F morning with a 65°F dew point, about {fs['8:00']} s/mi at 8:00 pace,
{fs['10:00']} s/mi at 10:00 and {fs['12:00']} s/mi at 12:00.</p></div>

<p class="lede">Heat slows running because your body has to spend effort shedding heat, and humid air makes that harder:
sweat only cools you when it evaporates. The dew point measures how much water is actually in the air, so it says more
about how a run will feel than the temperature or relative humidity alone.</p>

<h2>Pace cost by temperature + dew point</h2>
{sum_table("shade", "Seconds per mile added (or saved) against an ordinary 60°F day, in shade: overcast, early morning or evening. 5 mph wind, sea level.")}
<p class="note">A negative number is a gain: cool, dry air lets you run the same effort a little faster.
The split between temperature and dew point doesn't matter in this model; only their sum does.</p>

<h2>In full sun</h2>
<p>Direct sun adds a radiant load on top of the air temperature. In full midday sun (about {D['conditions']['sunSolarWm2']} W/m²) the cost is higher:</p>
{sum_table("sun", "Seconds per mile, full midday sun, 5 mph wind, sea level.")}
<p>At a 10:00/mile easy pace, 75°F with a 70°F dew point costs about {ex['humid_75_70_shade']} s/mi in shade and
{ex['humid_75_70_sun']} s/mi in sun. 85°F with a 70°F dew point in sun costs about {ex['hot_85_70_sun']} s/mi;
90°F with a 75°F dew point, about {ex['hot_90_75_sun']} s/mi.</p>

<h2>The full grid, 10:00/mile</h2>
{grid_table()}

<h2>Why slower runners lose more</h2>
<p>The classic temperature-plus-dew-point charts were built from competitive race results. Studies of marathon finishers
(Ely and colleagues, 2007) found the slowdown from heat grows down the field: the leaders lost under 1% per 5°C of WBGT,
while runners further back lost over 3%. A slower runner is out in the heat longer, and makes less of their own cooling airflow.
ArcPace scales the heat cost by your own easy pace, from 0.8× for fast runners up to 2.2× at about 13:40/mile.</p>

<h2>How these numbers are made</h2>
<ul>
<li>Pace cost is a percentage of your easy pace, from a temperature + dew point table, measured against an ordinary day (a sum of 120, about 60°F with a 60°F dew point, or a little warmer with drier air).</li>
<li>In sun, a radiant term is added from solar radiation, the same one used for WBGT.</li>
<li>When there's heat to shed, still air costs a little extra: a runner relies on airflow to cool.</li>
<li>Default heat tolerance (3 of 5). ArcPace lets you set yours from 1 to 5; each step moves the temperature + dew point sum by 6°F.</li>
<li>Wind, rain, snow and altitude add their own costs in the app; these tables hold them at 5 mph, dry and sea level.</li>
</ul>
<p class="note">These are estimates for planning easy runs, not medical advice. In real heat, slow down by feel, drink, and stop if you feel unwell.
For race-day risk, see <a href="/guides/wbgt-running-heat-flags/">WBGT and heat flags</a>.</p>
"""
pace_faq = [
    ("How much slower should I run in heat and humidity?",
     f"Add the temperature and dew point in °F. Below about 120 there's no cost, and at 120 only a few seconds. At a 10:00/mile easy pace, 140 adds about {s140} seconds per mile, 150 about {s150} and 160 about {s160}. Slower paces lose more."),
    ("Is dew point or humidity better for running?",
     "Dew point. Relative humidity depends on the temperature, so 90% at dawn can be comfortable and 50% in the afternoon miserable. Dew point measures the water in the air directly: under about 55°F feels fine, 60–65°F is noticeable, and 70°F or more is oppressive."),
    ("How much does 80 degrees slow running?",
     f"It depends on the dew point and your pace. At 80°F with a 65°F dew point, in shade, about {fs['8:00']} s/mi at 8:00 pace, {fs['10:00']} s/mi at 10:00 and {fs['12:00']} s/mi at 12:00."),
    ("Does running in the sun make a difference?",
     f"Yes. Full sun adds a radiant load. At a 10:00/mile pace, 75°F with a 70°F dew point costs about {ex['humid_75_70_shade']} s/mi in shade and {ex['humid_75_70_sun']} s/mi in sun."),
    ("Do you run faster in cool weather?",
     f"A little. Against an ordinary 60°F day, a cool, dry morning (50°F, dew point 35°F) is worth about {abs(ex['cool_50_35_shade'])} seconds per mile faster at a 10:00 easy pace."),
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
<li><strong>Wind</strong> strips heat fast. In the cold, a windproof layer matters more than a thicker one.</li>
<li><strong>Rain</strong> near freezing is the coldest running there is: add a shell and gloves even when the number looks mild.</li>
<li><strong>Sun and humidity</strong> push the warm side up: light colors, a cap and sunglasses, and plan water.</li>
<li><strong>You.</strong> Some runners run hot, some cold. ArcPace lets you set your cold and heat tolerance, and shifts the kit to match.</li>
<li><strong>Long runs</strong> start cold and finish warm. Pick layers you can take off and carry.</li>
</ul>
<p>This is the same rule ArcPace uses for every hour of the forecast: it dresses you for how the run will feel at mile two,
using the feels-like temperature, wind, rain and sun of the hour you plan to go out.</p>
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

<p class="lede">The thermometer reading says little about heat risk on its own. A 75°F morning in shade with dry air is pleasant;
75°F in full sun with a 70°F dew point is dangerous. WBGT weighs the things that actually limit how your body sheds heat:
humidity most of all (through the wet bulb), then sun (through the black globe), then the air.</p>

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
Not medical advice.</p>
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
          f"Add temperature and dew point (°F). Above 120, heat slows you: at a 10:00/mile pace, a sum of 150 adds about {s150} s/mi. Tables by pace, in shade and sun.",
          "How much do heat and humidity slow your running pace?", pace_body, pace_faq, "Heat, humidity and pace"),
     "How much do heat and humidity slow your running pace?",
     "Temperature + dew point tables for 8:00, 10:00 and 12:00 easy paces, in shade and sun."),
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
VALUES = {
    "s140": row[140]["shade"][i10], "s150": s150, "s160": s160,
    "sun_humid_shade": ex["humid_75_70_shade"], "sun_humid_sun": ex["humid_75_70_sun"],
}
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
     "Guides to running in the weather: staying cool in the heat, heat illness warning signs, cold, rain, wind, storms and smoke, plus pace, clothing and WBGT tables from the ArcPace model.",
     "Running weather guides",
     f"<p class='lede'>How the weather changes a run: practical guides, and reference tables with numbers from the model behind ArcPace.</p>"
     f"<h2>Running in the weather</h2><ul>{art_items}</ul><h2>Reference tables</h2><ul>{hub_items}</ul>",
     None, "Guides")

urls = ["", "guides/"] + [p for p, _, _ in ARTICLES] + [p for p, _, _ in GUIDES] + ["support/", "privacy/"]
sitemap = "\n".join(f"  <url><loc>{SITE}/{u}</loc><lastmod>{UPDATED}</lastmod></url>" for u in urls)
(ROOT / "sitemap.xml").write_text(
    f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sitemap}\n</urlset>\n')
print("built", len(GUIDES) + len(ARTICLES) + 1, "pages and sitemap.xml")
