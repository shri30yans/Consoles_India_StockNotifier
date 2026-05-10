"""aiohttp dashboard: live scrape status via Server-Sent Events."""

from __future__ import annotations

import asyncio
import json
import logging

from pathlib import Path

from aiohttp import web

from commerce_platform.observability.status import build_status_payload
from commerce_platform.platform.store.db import Database

logger = logging.getLogger(__name__)

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Commerce platform — scrape health</title>
  <style>
    :root {
      --bg: #0f1419;
      --panel: #1a2332;
      --border: #2d3a4f;
      --text: #e7ecf3;
      --muted: #8b9cb3;
      --ok: #3ecf8e;
      --warn: #e8c547;
      --stale: #e07a5f;
      --unknown: #7a8699;
      --accent: #5b9cf8;
    }
    * { box-sizing: border-box; }
    body {
      font-family: "Segoe UI", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 1.25rem 1.5rem 2rem;
      line-height: 1.45;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }
    h1 { font-size: 1.35rem; font-weight: 600; margin: 0; }
    .sub { color: var(--muted); font-size: 0.9rem; }
    #conn { font-size: 0.8rem; padding: 0.2rem 0.55rem; border-radius: 6px; background: var(--panel); }
    #conn.live { color: var(--ok); }
    #conn.dead { color: var(--stale); }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.65rem;
      margin-bottom: 1.25rem;
    }
    .stat {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.75rem 0.9rem;
    }
    .stat b { display: block; font-size: 1.45rem; font-weight: 600; }
    .stat span { color: var(--muted); font-size: 0.8rem; }
    section {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      margin-bottom: 1rem;
      overflow: hidden;
    }
    section h2 {
      margin: 0;
      padding: 0.75rem 1rem;
      font-size: 0.95rem;
      font-weight: 600;
      border-bottom: 1px solid var(--border);
      background: rgba(0,0,0,.15);
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { text-align: left; padding: 0.55rem 0.85rem; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 500; font-size: 0.78rem; text-transform: uppercase; letter-spacing: .04em; }
    tr:last-child td { border-bottom: none; }
    .pill {
      display: inline-block;
      padding: 0.15rem 0.45rem;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
    }
    .pill.ok { background: rgba(62, 207, 142, .2); color: var(--ok); }
    .pill.warn { background: rgba(232, 197, 71, .2); color: var(--warn); }
    .pill.stale { background: rgba(224, 122, 95, .2); color: var(--stale); }
    .pill.unknown { background: rgba(122, 134, 153, .2); color: var(--unknown); }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .mono { font-family: ui-monospace, monospace; font-size: 0.82rem; }
    .foot { color: var(--muted); font-size: 0.8rem; margin-top: 1rem; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Scrape health</h1>
      <p class="sub">Config from <span class="mono">platform.yaml</span> · evidence from SQLite · updates via SSE</p>
    </div>
    <div id="conn" class="dead">connecting…</div>
  </header>

  <div class="grid" id="summary"></div>

  <section>
    <h2>Product watches</h2>
    <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th>Health</th><th>Product</th><th>Retailer</th><th>Poll</th>
            <th>Last scrape</th><th>Stock</th><th>Price</th><th>URL</th>
          </tr>
        </thead>
        <tbody id="watches"></tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Platform sources (deals)</h2>
    <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th>Health</th><th>Type</th><th>Poll</th>
            <th>Last deal activity</th><th>Notes</th>
          </tr>
        </thead>
        <tbody id="sources"></tbody>
      </table>
    </div>
  </section>

  <p class="foot">
    <strong>Health</strong> compares time since last scrape (watches) or last recorded deal (aggregators)
    to <span class="mono">2×</span> and <span class="mono">5×</span> the configured poll interval:
    ok → warn → stale. REST: <a href="/api/status">/api/status</a>
  </p>

  <script>
    const $ = (id) => document.getElementById(id);
    function rel(iso) {
      if (!iso) return "—";
      const t = new Date(iso).getTime();
      if (Number.isNaN(t)) return iso;
      let s = Math.floor((Date.now() - t) / 1000);
      if (s < 60) return s + "s ago";
      if (s < 3600) return Math.floor(s/60) + "m ago";
      if (s < 86400) return Math.floor(s/3600) + "h ago";
      return Math.floor(s/86400) + "d ago";
    }
    function pill(h) {
      return '<span class="pill ' + h + '">' + h + '</span>';
    }
    function fmtPoll(s) {
      if (s >= 3600) return (s/3600).toFixed(1).replace(/\\.0$/,'') + 'h';
      if (s >= 60) return Math.round(s/60) + 'm';
      return s + 's';
    }
    function render(data) {
      const sm = data.summary || {};
      $('summary').innerHTML = [
        ['Watches (ok)', sm.product_watches_ok, 'of ' + (sm.product_watches_total||0)],
        ['Warn', sm.product_watches_warn, 'stretched interval'],
        ['Stale', sm.product_watches_stale, 'likely stuck or off'],
        ['Unknown', sm.product_watches_unknown, 'no DB row yet'],
        ['Platform sources', sm.platform_sources_total, 'deal ingestors'],
      ].map(([a,b,c]) => '<div class="stat"><b>'+b+'</b><span>'+a+' · '+c+'</span></div>').join('');

      $('watches').innerHTML = (data.watches||[]).map(w => {
        const short = (w.url||'').length > 42 ? (w.url||'').slice(0,40)+'…' : (w.url||'');
        return '<tr><td>'+pill(w.health)+'</td><td title="'+escapeHtml(w.product_id)+'">'+
          escapeHtml(w.product_name||'')+'</td><td class="mono">'+escapeHtml(w.retailer||'')+'</td><td>'+
          fmtPoll(w.poll_seconds||0)+'</td><td><span title="'+escapeHtml(w.last_scrape_at||'')+'">'+
          rel(w.last_scrape_at)+'</span></td><td>'+
          (w.in_stock===null||w.in_stock===undefined ? '—' : (w.in_stock ? 'in' : 'out'))+'</td><td>'+
          (w.price_inr!=null ? '₹'+Number(w.price_inr).toLocaleString('en-IN') : '—')+'</td><td><a href="'+escapeHtml(w.url||'#')+'" target="_blank" rel="noopener">'+escapeHtml(short)+'</a></td></tr>';
      }).join('') || '<tr><td colspan="8">No watches in config.</td></tr>';

      $('sources').innerHTML = (data.platform_sources||[]).map(s => {
        const note = (s.deal_stats && s.deal_stats.deals_recorded_last_24h != null)
          ? ('deals 24h: ' + s.deal_stats.deals_recorded_last_24h)
          : (s.url ? 'url configured' : '—');
        return '<tr><td>'+pill(s.health)+'</td><td class="mono">'+escapeHtml(s.type||'')+'</td><td>'+
          fmtPoll(s.poll_seconds||0)+'</td><td><span title="'+escapeHtml(s.last_deal_activity_at||'')+'">'+
          rel(s.last_deal_activity_at)+'</span></td><td>'+escapeHtml(note)+'</td></tr>';
      }).join('') || '<tr><td colspan="5">No platform_sources in config.</td></tr>';
    }
    function escapeHtml(t) {
      if (!t) return '';
      const d = document.createElement('div');
      d.textContent = t;
      return d.innerHTML;
    }

    let es;
    function connect() {
      es = new EventSource('/api/stream');
      es.onopen = () => { $('conn').textContent = 'live · SSE'; $('conn').className = 'live'; };
      es.onmessage = (ev) => { try { render(JSON.parse(ev.data)); } catch (e) {} };
      es.onerror = () => {
        $('conn').textContent = 'reconnecting…'; $('conn').className = 'dead';
        es.close();
        setTimeout(connect, 2500);
      };
    }
    connect();
    setInterval(() => {
      const tbody = $('watches');
      if (tbody && tbody.rows.length) { /* re-touch rel() by re-fetch from last payload — lightweight tick */
        const ev = new CustomEvent('tick');
        document.dispatchEvent(ev);
      }
    }, 30000);

    fetch('/api/status').then(r=>r.json()).then(render).catch(()=>{});
  </script>
</body>
</html>
"""


async def run_dashboard(yaml_path: str | Path, db: Database, host: str, port: int) -> None:
    path = Path(yaml_path)

    async def handle_index(_request: web.Request) -> web.StreamResponse:
        return web.Response(text=INDEX_HTML, content_type="text/html; charset=utf-8")

    async def handle_api(_request: web.Request) -> web.Response:
        payload = await build_status_payload(path, db)
        return web.json_response(payload)

    async def handle_stream(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)
        try:
            while True:
                if request.transport is not None and request.transport.is_closing():
                    break
                payload = await build_status_payload(path, db)
                line = "data: " + json.dumps(payload) + "\n\n"
                await response.write(line.encode())
                await asyncio.sleep(2.5)
        except (asyncio.CancelledError, ConnectionError, OSError):
            pass
        return response

    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_api)
    app.router.add_get("/api/stream", handle_stream)

    async def on_cleanup(_app: web.Application) -> None:
        await db.close()

    app.on_cleanup.append(on_cleanup)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Scrape dashboard at http://%s:%s/", host, port)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

