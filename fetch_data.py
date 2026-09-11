#!/usr/bin/env python3
"""
Portfolio live updater.

Reads the HOLDINGS list below, fetches the latest price for each stock from
Yahoo Finance, pulls a few recent news headlines per stock from Google News,
computes profit/loss, and writes everything into data.json.

The dashboard (index.html) reads data.json and shows it. This script is meant
to be run on a schedule by GitHub Actions (see .github/workflows/update.yml),
but you can also run it by hand:  python fetch_data.py

To ADD or EDIT a holding, just change the HOLDINGS list. Each row is:
    (Display name, Yahoo symbol, quantity, average buy price)

Yahoo symbols:  NSE stocks end with .NS   (e.g. RELIANCE.NS)
                BSE stocks end with .BO   (e.g. SAMRATPH.BO)
If a stock shows "check symbol" on the dashboard, the Yahoo symbol here is
wrong for that stock. Fix it in this list and the next run corrects it.
"""

import json
import sys
import time
import datetime
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# YOUR HOLDINGS  ->  (name, yahoo_symbol, quantity, avg_price)
# yahoo_symbol = None  means "symbol not set yet" (row shows, price stays blank)
# ---------------------------------------------------------------------------
HOLDINGS = [
    # --- from the Angel One screenshot ---
    ("Ceinsys Tech",              "CEINSYS.NS",     50,   1390.63),
    ("EPACK Durable",             "EPACK.NS",       300,  393.77),
    ("Jio Financial (lot 1)",     "JIOFIN.NS",      660,  295.33),
    ("MosChip Technologies",      "MOSCHIP.NS",     349,  230.14),
    ("Salzer Electronics",        "SALZERELEC.NS",  129,  967.03),
    ("Samrat Pharmachem",         "SAMRATPH.BO",    266,  369.95),   # trades on BSE
    ("Veefin Solutions (lot 1)",  "VEEFIN.NS",      600,  306.07),

    # --- from your list ---
    ("Azad Engineering",          "AZAD.NS",        175,  1672.92),
    ("Unimech Aerospace",         "UNIMECH.NS",     200,  1295.44),
    ("Avalon Technologies",       "AVALON.NS",      153,  981.05),
    ("Veefin Solutions (lot 2)",  "VEEFIN.NS",      200,  310.18),
    ("Apollo Micro Systems",      "APOLLO.NS",      500,  103.38),
    ("IDBI Bank",                 "IDBI.NS",        2100, 70.62),
    ("Singer India",              "SINGER.NS",      900,  91.03),
    ("Lokesh Machines",           "LOKESHMACH.NS",  100,  423.68),
    ("Sterlite Technologies",     "STLTECH.NS",     500,  71.29),
    ("Zaggle Prepaid Ocean",      "ZAGGLE.NS",      200,  365.11),
    ("Dish TV India",             "DISHTV.NS",      4750, 14.45),
    ("Ashoka Buildcon",           "ASHOKA.NS",      945,  224.49),
    ("DAM Capital Advisors",      "DAMCAPITAL.NS",  1098, 227.606),
    ("PG Electroplast",           "PGEL.NS",        160,  744.00),
    ("Nila Spaces",               "NILASPACES.NS",  2320, 8.38),
    ("Himadri Speciality Chem",   "HSCL.NS",        200,  495.42),
    ("Bajaj Healthcare",          "BAJAJHCARE.NS",  100,  690.52),
    ("Shree Renuka Sugars",       "RENUKA.NS",      1500, 54.15),
    ("KFin Technologies",         "KFINTECH.NS",    70,   655.89),
    ("Salasar Techno Engg",       "SALASAR.NS",     1014, 22.75),
    ("Orient Green Power",        "OGPL.NS",        1000, 23.00),
    ("Rail Vikas Nigam",          "RVNL.NS",        175,  505.11),
    ("Gateway Distriparks",       "GATEWAY.NS",     218,  113.90),
    ("Lancer Container Lines",    "LANCERCON.NS",   830,  60.21),    # <-- verify symbol on first run
    ("HUDCO",                     "HUDCO.NS",       269,  292.49),
    ("PNC Infratech",             "PNCINFRA.NS",    380,  386.90),
    ("Jio Financial (lot 2)",     "JIOFIN.NS",      645,  263.25),
    ("Himatsingka Seide",         "HIMATSEIDE.NS",  660,  176.77),
    ("IREDA",                     "IREDA.NS",       580,  191.95),
    ("IDFC First Bank",           "IDFCFIRSTB.NS",  1650, 71.73),
    ("Vishnu Prakash R Punglia",  "VPRPL.NS",       1360, 201.54),
    ("Techno Electric & Engg",    "TECHNOE.NS",     121,  1296.40),
    ("Ganesh Ecosphere",          "GANECOS.NS",     50,   1557.12),
    ("Shakti Pumps India",        "SHAKTIPUMP.NS",  180,  767.67),
    ("Astra Microwave Products",  "ASTRAMICRO.NS",  111,  869.93),
    ("Reliance Industries",       "RELIANCE.NS",    110,  1313.21),
    ("Welspun Corp",              "WELCORP.NS",     60,   545.45),

    # --- from the second account screenshot ---
    ("IFCI",                      "IFCI.NS",        2640, 82.41),
    ("SITI Networks",             "SITINET.NS",     352,  0.86),
    ("Frontline Corporation",     "FRONTCORP.NS",   20,   46.83),    # <-- thin stock, may need symbol fix
]

HEADERS = {"User-Agent": "Mozilla/5.0 (portfolio-dashboard)"}


def fetch_quote(symbol):
    """Return (last_price, prev_close) for a Yahoo symbol, or (None, None)."""
    if not symbol:
        return None, None
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol) + "?range=2d&interval=1d")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        result = data["chart"]["result"][0]
        meta = result["meta"]
        last = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        return last, prev
    except Exception as e:
        print(f"  ! price failed for {symbol}: {e}", file=sys.stderr)
        return None, None


def fetch_news(name, limit=3):
    """Return a list of {title, link, source, when} from Google News RSS."""
    q = urllib.parse.quote(f'"{name}" stock share')
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub = item.findtext("pubDate", "")
            src_el = item.find("source")
            source = src_el.text if src_el is not None else ""
            items.append({"title": title, "link": link,
                          "source": source, "when": pub})
            if len(items) >= limit:
                break
    except Exception as e:
        print(f"  ! news failed for {name}: {e}", file=sys.stderr)
    return items


def build():
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist)

    rows = []
    tot_inv = tot_cur = tot_day = 0.0
    total_cost = 0.0   # cost basis of every holding, priced or not
    pending = 0

    for name, sym, qty, avg in HOLDINGS:
        print(f"- {name} ({sym})")
        last, prev = fetch_quote(sym)
        invested = qty * avg
        total_cost += invested
        row = {
            "name": name, "symbol": sym, "qty": qty, "avg": avg,
            "ltp": last, "prev_close": prev, "invested": round(invested, 2),
            "news": fetch_news(name),
        }
        if last is not None:
            cur = qty * last
            row["current"] = round(cur, 2)
            row["pnl"] = round(cur - invested, 2)
            row["pnl_pct"] = round((cur - invested) / invested * 100, 2) if invested else 0
            if prev:
                row["day_pnl"] = round(qty * (last - prev), 2)
                row["day_pct"] = round((last - prev) / prev * 100, 2)
                tot_day += qty * (last - prev)
            # only count in the P&L totals when we have a live price,
            # so invested and current always cover the same set of stocks
            tot_inv += invested
            tot_cur += cur
        else:
            row["current"] = None
            row["pnl"] = None
            row["pnl_pct"] = None
            pending += 1
        rows.append(row)
        time.sleep(0.3)  # be gentle on the free endpoints

    summary = {
        "invested": round(tot_inv, 2),
        "current": round(tot_cur, 2),
        "pnl": round(tot_cur - tot_inv, 2),
        "pnl_pct": round((tot_cur - tot_inv) / tot_inv * 100, 2) if tot_inv else 0,
        "day_pnl": round(tot_day, 2),
        "total_cost": round(total_cost, 2),
        "pending": pending,
        "count": len(rows),
        "updated": now.strftime("%d %b %Y, %I:%M %p IST"),
    }

    with open("data.json", "w") as f:
        json.dump({"summary": summary, "holdings": rows}, f, indent=2)
    print(f"\nWrote data.json  |  {len(rows)} holdings  |  updated {summary['updated']}")


if __name__ == "__main__":
    build()
