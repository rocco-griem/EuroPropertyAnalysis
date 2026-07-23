"""Photo-real, scroll-driven day->night Europe map hero for the Overview page.

Returns an HTML string (embed with `streamlit.components.v1.html`). The base imagery is real
NASA satellite photography — Blue Marble (daylight) and VIIRS Black Marble (night lights),
fetched once by `src/tools/fetch_map_imagery.py` into `dashboard/static/` and served by
Streamlit's static-file feature (`enableStaticServing`, see `.streamlit/config.toml`). A trimmed
real-geography Europe outline (`assets/europe.geojson`, Natural Earth 110m) is drawn as a subtle
border overlay on top of the photo, plus every "capital"/"city" place from `settings.PLACES`
(via `hero_assets.cities_json()` — "island" places like Mallorca don't get a city light here).

The day->night transition is driven by scrolling *within the hero's own scroll region* (a sticky
map over a tall track): Streamlit component iframes can't read the outer page's scroll position,
so this is the reliable realisation of the scroll-linked effect. As you scroll, a soft terminator
band sweeps west->east across the map, and each capital lights up as a glowing amber "city light"
right as the terminator reaches it (so London lights before Warsaw). `prefers-reduced-motion`
users get the night state immediately, without the scroll dependency.

If the satellite imagery fails to load (e.g. static serving misconfigured), the hero falls back to
flat vector fills so it never renders blank.
"""

from __future__ import annotations

import json
from pathlib import Path

from components import hero_assets, theme

_GEOJSON_PATH = Path(__file__).resolve().parent / "assets" / "europe.geojson"


def _europe_geometry() -> str:
    return _GEOJSON_PATH.read_text(encoding="utf-8")


def render() -> str:
    """Build the hero map HTML (embed with `st.components.v1.html(render(), height=..., scrolling=False)`)."""
    return _TEMPLATE.format(
        geo=_europe_geometry(),
        cities=hero_assets.cities_json(),
        day_url=hero_assets.static_url(hero_assets.EUROPE_DAY),
        night_url=hero_assets.static_url(hero_assets.EUROPE_NIGHT),
        europe_lon=json.dumps(list(hero_assets.EUROPE_LON)),
        europe_lat=json.dumps(list(hero_assets.EUROPE_LAT)),
        accent=theme.ACCENT,
        accent_light=theme.ACCENT_LIGHT,
        bg=theme.BACKGROUND,
    )


_TEMPLATE = r"""
<div class="hero-wrap" id="heroWrap">
  <div class="hero-sticky">
    <canvas id="heroCanvas"></canvas>
    <div class="hero-caption">
      <span class="hero-eyebrow">10 European cities</span>
      <span class="hero-hint" id="heroHint">Scroll ↓ &nbsp;day to night</span>
      <span class="hero-credit">Imagery: NASA Blue Marble / Black Marble (VIIRS)</span>
    </div>
  </div>
  <div class="hero-track"></div>
</div>

<style>
  html, body {{ margin: 0; padding: 0; height: 100%; background: {bg}; overflow: hidden; }}
  * {{ box-sizing: border-box; }}
  .hero-wrap {{
    height: 100vh; overflow-y: scroll; overflow-x: hidden; position: relative;
    scrollbar-width: none; border-radius: 16px;
  }}
  .hero-wrap::-webkit-scrollbar {{ width: 0; height: 0; }}
  .hero-sticky {{ position: sticky; top: 0; height: 100vh; width: 100%; }}
  #heroCanvas {{ display: block; width: 100%; height: 100%; border-radius: 16px; }}
  .hero-track {{ height: 260vh; }}
  .hero-caption {{
    position: absolute; left: 18px; bottom: 16px; display: flex; flex-direction: column;
    gap: 4px; font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
    pointer-events: none;
  }}
  .hero-eyebrow {{
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    color: rgba(230,233,239,0.75);
  }}
  .hero-hint {{
    font-size: 0.8rem; color: {accent_light}; opacity: 0.85;
    transition: opacity 0.4s ease;
  }}
  .hero-credit {{
    font-size: 0.65rem; color: rgba(230,233,239,0.45);
  }}
</style>

<script>
(function() {{
  const GEO = {geo};
  const CITIES = {cities};
  const ACCENT = "{accent}";
  const ACCENT_LIGHT = "{accent_light}";
  const DAY_URL = "{day_url}";
  const NIGHT_URL = "{night_url}";
  const EUROPE_LON = {europe_lon};   // [min, max] — must match src/tools/fetch_map_imagery.py
  const EUROPE_LAT = {europe_lat};   // [min, max]

  const wrap = document.getElementById('heroWrap');
  const canvas = document.getElementById('heroCanvas');
  const hint = document.getElementById('heroHint');
  const ctx = canvas.getContext('2d');
  const maskCanvas = document.createElement('canvas');
  const maskCtx = maskCanvas.getContext('2d');

  // Latitude band that must always be fully visible (covers Madrid ~40.4 up to Warsaw/London
  // ~52.5 with margin) and the longitude to centre on; the width is filled from there so the
  // map is full-bleed at any aspect without ever cropping a capital north/south.
  const LAT_TOP = 55.5, LAT_BOTTOM = 37.5, CENTER_LON = 8.5;
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Web-Mercator: both axes in the same (radian) unit so the aspect ratio is correct.
  function mercX(lon) {{ return lon * Math.PI/180; }}
  function mercY(lat) {{ return Math.log(Math.tan(Math.PI/4 + (lat*Math.PI/180)/2)); }}

  let W = 0, H = 0, proj = null;
  function computeProjection() {{
    const dpr = window.devicePixelRatio || 1;
    W = wrap.clientWidth; H = wrap.clientHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    maskCanvas.width = canvas.width; maskCanvas.height = canvas.height;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    maskCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const yTop = mercY(LAT_TOP), yBot = mercY(LAT_BOTTOM);
    const s = H / (yTop - yBot);        // fill the height with the required latitude band
    const cx = mercX(CENTER_LON);
    proj = function(lon, lat) {{
      return [ W/2 + (mercX(lon) - cx) * s, (yTop - mercY(lat)) * s ];
    }};
  }}

  function lerp(a, b, t) {{ return a + (b - a) * t; }}
  function mix(c1, c2, t) {{
    return 'rgb(' + Math.round(lerp(c1[0],c2[0],t)) + ',' + Math.round(lerp(c1[1],c2[1],t))
         + ',' + Math.round(lerp(c1[2],c2[2],t)) + ')';
  }}
  function clamp(v, lo, hi) {{ return Math.max(lo, Math.min(hi, v)); }}
  function smoothstep(t) {{ t = clamp(t, 0, 1); return t*t*(3 - 2*t); }}

  // Palettes for the vector border overlay and the fallback flat fills: [day, night].
  const SEA   = [[169,211,232], [6,9,16]];
  const LAND  = [[232,228,216], [18,22,31]];
  const BORDER= [[201,195,178], [40,48,62]];
  const CITYD = [107,116,128];       // daytime dot (muted slate)

  function hexToRgb(h) {{ const n = parseInt(h.slice(1),16); return [(n>>16)&255,(n>>8)&255,n&255]; }}
  const ACCENT_RGB = hexToRgb(ACCENT_LIGHT);

  // --- Satellite imagery -----------------------------------------------------------------
  const dayImg = new Image();
  const nightImg = new Image();
  let imagesReady = 0, imagesFailed = false;
  function onImgReady() {{ imagesReady++; requestDraw(); }}
  function onImgFail() {{ imagesFailed = true; requestDraw(); }}
  dayImg.onload = onImgReady; dayImg.onerror = onImgFail; dayImg.src = DAY_URL;
  nightImg.onload = onImgReady; nightImg.onerror = onImgFail; nightImg.src = NIGHT_URL;

  // Destination rect (canvas px) the Europe crop is drawn into, from its known geo bounds.
  function destRect() {{
    const topLeft = proj(EUROPE_LON[0], EUROPE_LAT[1]);
    const botRight = proj(EUROPE_LON[1], EUROPE_LAT[0]);
    return {{ x: topLeft[0], y: topLeft[1], w: botRight[0] - topLeft[0], h: botRight[1] - topLeft[1] }};
  }}

  function drawPolygon(rings, fill) {{
    for (const ring of rings) {{
      ctx.beginPath();
      for (let i=0;i<ring.length;i++) {{
        const p = proj(ring[i][0], ring[i][1]);
        if (i===0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
      }}
      ctx.closePath();
      if (fill) ctx.fill();
      ctx.stroke();
    }}
  }}

  // Fallback: today's flat vector fills, used only if the satellite imagery fails to load.
  function drawFallbackLand(p) {{
    ctx.fillStyle = mix(SEA[0], SEA[1], p);
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = mix(LAND[0], LAND[1], p);
    ctx.strokeStyle = mix(BORDER[0], BORDER[1], p);
    ctx.lineWidth = 0.7;
    ctx.lineJoin = 'round';
    for (const g of GEO.geometries) {{
      if (g.type === 'Polygon') drawPolygon(g.coordinates, true);
      else if (g.type === 'MultiPolygon') for (const poly of g.coordinates) drawPolygon(poly, true);
    }}
  }}

  // Subtle country-border overlay drawn on top of the photo (stroke only, no fill).
  function drawBorderOverlay(p) {{
    ctx.strokeStyle = mix(BORDER[0], BORDER[1], p);
    ctx.globalAlpha = 0.5;
    ctx.lineWidth = 0.6;
    ctx.lineJoin = 'round';
    for (const g of GEO.geometries) {{
      if (g.type === 'Polygon') drawPolygon(g.coordinates, false);
      else if (g.type === 'MultiPolygon') for (const poly of g.coordinates) drawPolygon(poly, false);
    }}
    ctx.globalAlpha = 1;
  }}

  let progress = 0;
  // Terminator: a soft band (in canvas px) whose centre sweeps from off-screen-left to
  // off-screen-right as `progress` goes 0 -> 1, revealing the night image to its west.
  function terminatorEdge(band) {{ return -band/2 + progress * (W + band); }}

  function draw() {{
    if (!proj) return;
    const p = progress; // 0 day -> 1 night, used only for the border tint and vignette strength
    const rect = destRect();

    if (imagesFailed) {{
      drawFallbackLand(p);
    }} else if (imagesReady < 2) {{
      ctx.fillStyle = '{bg}';
      ctx.fillRect(0, 0, W, H);
    }} else {{
      ctx.drawImage(dayImg, rect.x, rect.y, rect.w, rect.h);
      const band = Math.max(40, W * 0.18);
      const edge = terminatorEdge(band);
      maskCtx.clearRect(0, 0, W, H);
      maskCtx.drawImage(nightImg, rect.x, rect.y, rect.w, rect.h);
      maskCtx.globalCompositeOperation = 'destination-in';
      const grad = maskCtx.createLinearGradient(edge - band/2, 0, edge + band/2, 0);
      grad.addColorStop(0, 'rgba(0,0,0,1)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      maskCtx.fillStyle = grad;
      maskCtx.fillRect(0, 0, W, H);
      maskCtx.globalCompositeOperation = 'source-over';
      ctx.drawImage(maskCanvas, 0, 0, W, H);
    }}

    // subtle top-down vignette that deepens at night
    const grad2 = ctx.createRadialGradient(W*0.5, H*0.45, Math.min(W,H)*0.2, W*0.5, H*0.5, Math.max(W,H)*0.75);
    grad2.addColorStop(0, 'rgba(0,0,0,0)');
    grad2.addColorStop(1, 'rgba(0,0,0,' + (0.10 + 0.35*p) + ')');
    ctx.fillStyle = grad2; ctx.fillRect(0, 0, W, H);

    if (!imagesFailed && imagesReady >= 2) drawBorderOverlay(p);

    // Cities: each capital's glow follows the terminator past its own position, so westerly
    // cities (London) light up before easterly ones (Warsaw) as the band sweeps through.
    const band = Math.max(40, W * 0.18);
    const edge = terminatorEdge(band);
    const pulse = reduceMotion ? 1 : (0.85 + 0.15*Math.sin(Date.now()/650));
    ctx.textBaseline = 'middle';
    ctx.font = '600 12px Inter, system-ui, sans-serif';
    for (const c of CITIES) {{
      const q = proj(c.lon, c.lat);
      const glow = smoothstep((edge - q[0]) / band + 0.5);
      if (glow > 0.01) {{
        const r = (10 + 16*glow) * pulse;
        const rg = ctx.createRadialGradient(q[0], q[1], 0, q[0], q[1], r);
        rg.addColorStop(0, 'rgba(' + ACCENT_RGB[0] + ',' + ACCENT_RGB[1] + ',' + ACCENT_RGB[2] + ',' + (0.55*glow) + ')');
        rg.addColorStop(1, 'rgba(' + ACCENT_RGB[0] + ',' + ACCENT_RGB[1] + ',' + ACCENT_RGB[2] + ',0)');
        ctx.fillStyle = rg;
        ctx.beginPath(); ctx.arc(q[0], q[1], r, 0, Math.PI*2); ctx.fill();
      }}
      // core dot: muted by day -> bright amber by night
      const dotR = 3.2 + 1.3*glow;
      ctx.beginPath(); ctx.arc(q[0], q[1], dotR, 0, Math.PI*2);
      ctx.fillStyle = glow > 0.5 ? '#FFF3E4' : mix(CITYD, ACCENT_RGB, glow);
      ctx.fill();
      // label
      const lx = q[0] + dotR + 5, ly = q[1];
      ctx.fillStyle = 'rgba(' + Math.round(lerp(90,242,glow)) + ',' + Math.round(lerp(99,166,glow))
        + ',' + Math.round(lerp(112,90,glow)) + ',' + (0.6 + 0.4*glow) + ')';
      ctx.fillText(c.name, lx, ly);
    }}
  }}

  function onScroll() {{
    const max = wrap.scrollHeight - wrap.clientHeight;
    progress = max > 0 ? Math.min(1, Math.max(0, wrap.scrollTop / max)) : 0;
    if (hint) hint.style.opacity = String(Math.max(0, 0.85 - progress*1.3));
    requestDraw();
  }}

  let raf = null;
  function requestDraw() {{ if (raf) return; raf = requestAnimationFrame(function() {{ raf = null; draw(); }}); }}

  function resize() {{ computeProjection(); draw(); }}

  window.addEventListener('resize', resize);
  wrap.addEventListener('scroll', onScroll, {{ passive: true }});

  computeProjection();
  if (reduceMotion) {{ progress = 1; draw(); }}
  else {{
    draw();
    // gentle pulsing of the night lights
    setInterval(function() {{ if (progress > 0.15) requestDraw(); }}, 90);
  }}
}})();
</script>
"""
