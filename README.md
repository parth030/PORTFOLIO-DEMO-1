# My Portfolio — live dashboard

A single-page dashboard that shows your holdings, live-ish prices, profit/loss
and recent news. It updates itself every 15 minutes while the market is open,
and you can open it from any phone or laptop through a link.

## What each file does

| File | Purpose |
|---|---|
| `index.html` | The dashboard you look at. Reads `data.json`. |
| `data.json` | The numbers and news. Refreshed automatically. |
| `fetch_data.py` | Gets prices + news and rewrites `data.json`. Your holdings live here. |
| `.github/workflows/update.yml` | Runs the fetcher every 15 min during market hours. |

## One-time setup (about 5 minutes)

1. Create a **public** repository on GitHub (e.g. `portfolio`). Tip: naming it
   `parth030.github.io` makes the link cleaner.
2. Upload all four files, keeping the `.github/workflows/` folder structure.
3. Go to **Settings → Pages**, set Source to **Deploy from a branch**, pick the
   `main` branch and `/ (root)` folder, and Save. Your link appears in a minute,
   like `parth030.github.io/portfolio`.
4. Go to the **Actions** tab, and if prompted, enable workflows. Open
   **Update portfolio data** and click **Run workflow** once to pull the first
   set of live prices and news. After that it runs on its own.

That's it. Open the link on your phone and use **Add to Home Screen** so it sits
like an app.

## Editing your holdings

Open `fetch_data.py` and edit the `HOLDINGS` list. Each line is:

```python
("Display name", "YAHOO_SYMBOL", quantity, average_price),
```

- NSE stocks end in `.NS` (e.g. `RELIANCE.NS`), BSE stocks end in `.BO`.
- If a stock shows **"check symbol"** on the dashboard, its Yahoo symbol is
  wrong — fix it here and the next run corrects it.
- Two lines still need you: **Dharan** (set its real symbol) and a couple marked
  "verify symbol" in the file.

Commit the change and the dashboard updates on the next run.

## Good to know

- Prices are **delayed**, not tick-by-tick. Real-time NSE/BSE feeds are a paid,
  licensed product; this free setup is fine for watching through the day.
- GitHub pauses scheduled jobs if a repo sees no activity for 60 days. Any commit
  (or a manual run from the Actions tab) wakes it back up.
- This is a personal tracker for information only, not investment advice.
