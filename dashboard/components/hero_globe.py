"""Photo-real, scroll-driven 3D rotating-globe hero for the Overview page (alternative to the flat
Web-Mercator hero in `hero_map.py` — see `views/overview.py`'s toggle between the two).

Textured with the same NASA satellite imagery as the flat hero (Blue Marble day / VIIRS Black
Marble night, fetched by `src/tools/fetch_map_imagery.py`), but rendered as an actual sphere in
raw WebGL — no three.js. A globe is one full-screen quad plus a per-pixel ray/sphere-intersection
fragment shader (orthographic projection), which is ~100 lines of GLSL; vendoring a ~600 KB 3D
library to draw one sphere would work against keeping this dashboard small and offline-capable.

The hero plays as a single sequence, driven by scroll within its own scroll region (same
sticky-over-tall-track mechanic as `hero_map`):
  1. Before any scroll, the globe sits zoomed out ("in space") and idle-spins on its own via a
     time-based `requestAnimationFrame` loop.
  2. The first scroll freezes the idle spin and hands rotation over to scroll position: scrolling
     zooms the globe in while it finishes rotating onto Europe, continuing seamlessly from
     wherever the idle spin left off (no jump).
  3. The zoom lands at the same lat-band framing `hero_map.py` uses (`LAT_TOP`/`LAT_BOTTOM` around
     `CENTER_LON`), computed at runtime from the same forward-projection math used for city
     markers. Once landed (tracked via a high-water-mark on scroll progress), rotation and zoom
     lock — scrolling back up cannot re-zoom or re-spin.
  4. Only then does further scroll drive the day->night terminator sweep — a physically-shaped
     terminator (`dot(surface normal, sun direction)`, not a crossfade) — bidirectionally, exactly
     like before.
The 9 capitals are projected to screen space with the same rotation math and drawn as a 2D canvas
overlay on top of the WebGL canvas (hidden once they rotate to the far side of the globe).

If WebGL is unavailable, falls back to a plain 2D vector silhouette of Europe (reusing
`assets/europe.geojson`) so the hero never renders blank.
"""

from __future__ import annotations

from pathlib import Path

from components import hero_assets, theme

_GEOJSON_PATH = Path(__file__).resolve().parent / "assets" / "europe.geojson"

# Roughly the geographic centre of the 9 capitals (Madrid 40.4N to Warsaw 52.2N; -3.7E to 21.0E)
# — where the globe faces at the start of the scroll range. Kept independent of hero_map.py's
# CENTER_LON (same value, 8.5) since the two heroes are otherwise decoupled.
EUROPE_CENTER_LON_DEG = 8.5
EUROPE_CENTER_LAT_DEG = 47.0


def _europe_geometry() -> str:
    return _GEOJSON_PATH.read_text(encoding="utf-8")


def render() -> str:
    """Build the globe hero HTML (embed with `st.components.v1.html(render(), height=..., scrolling=False)`)."""
    html = _TEMPLATE
    html = html.replace("__GEO__", _europe_geometry())
    html = html.replace("__CITIES__", hero_assets.cities_json())
    html = html.replace("__DAY_URL__", hero_assets.static_url(hero_assets.EARTH_DAY))
    html = html.replace("__NIGHT_URL__", hero_assets.static_url(hero_assets.EARTH_NIGHT))
    html = html.replace("__ACCENT__", theme.ACCENT)
    html = html.replace("__ACCENT_LIGHT__", theme.ACCENT_LIGHT)
    html = html.replace("__BG__", theme.BACKGROUND)
    html = html.replace("__CENTER_LON_DEG__", str(EUROPE_CENTER_LON_DEG))
    html = html.replace("__CENTER_LAT_DEG__", str(EUROPE_CENTER_LAT_DEG))
    return html


_TEMPLATE = r"""
<div class="hero-wrap" id="heroWrap">
  <div class="hero-sticky">
    <canvas id="glCanvas"></canvas>
    <canvas id="overlayCanvas"></canvas>
    <div class="hero-caption">
      <span class="hero-eyebrow">10 European cities &mdash; globe</span>
      <span class="hero-hint" id="heroHint">Scroll &darr; &nbsp;zoom into Europe</span>
      <span class="hero-credit">Imagery: NASA Blue Marble / Black Marble (VIIRS)</span>
    </div>
  </div>
  <div class="hero-track"></div>
</div>

<style>
  html, body { margin: 0; padding: 0; height: 100%; background: __BG__; overflow: hidden; }
  * { box-sizing: border-box; }
  .hero-wrap {
    height: 100vh; overflow-y: scroll; overflow-x: hidden; position: relative;
    scrollbar-width: none; border-radius: 16px; background: __BG__;
  }
  .hero-wrap::-webkit-scrollbar { width: 0; height: 0; }
  .hero-sticky { position: sticky; top: 0; height: 100vh; width: 100%; }
  #glCanvas, #overlayCanvas {
    display: block; position: absolute; inset: 0; width: 100%; height: 100%; border-radius: 16px;
  }
  #overlayCanvas { pointer-events: none; }
  .hero-track { height: 340vh; }
  .hero-caption {
    position: absolute; left: 18px; bottom: 16px; display: flex; flex-direction: column;
    gap: 4px; font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
    pointer-events: none; z-index: 2;
  }
  .hero-eyebrow {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    color: rgba(230,233,239,0.75);
  }
  .hero-hint { font-size: 0.8rem; color: __ACCENT_LIGHT__; opacity: 0.85; transition: opacity 0.4s ease; }
  .hero-credit { font-size: 0.65rem; color: rgba(230,233,239,0.45); }
</style>

<script>
(function() {
  const GEO = __GEO__;
  const CITIES = __CITIES__;
  const ACCENT_LIGHT = "__ACCENT_LIGHT__";
  const DAY_URL = "__DAY_URL__";
  const NIGHT_URL = "__NIGHT_URL__";
  const CENTER_LON_DEG = __CENTER_LON_DEG__;
  const CENTER_LON = __CENTER_LON_DEG__ * Math.PI / 180;
  const CENTER_LAT = __CENTER_LAT_DEG__ * Math.PI / 180;
  const ZOOM_OUT_RADIUS = 0.42; // fraction of min(W,H)/2 — "planet in space" starting framing
  // Lat band that must fill the viewport height once landed — must match hero_map.py's
  // LAT_TOP/LAT_BOTTOM so the globe's landed framing matches the flat map's exactly.
  const LAT_TOP = 55.5, LAT_BOTTOM = 37.5;
  let landedRadius = 0.86; // recomputed per-viewport in resize(), via computeLandedRadius()
  const ZOOM_PHASE_END = 0.4; // fraction of scroll spent zooming in vs. driving day/night

  const wrap = document.getElementById('heroWrap');
  const glCanvas = document.getElementById('glCanvas');
  const overlay = document.getElementById('overlayCanvas');
  const hint = document.getElementById('heroHint');
  const octx = overlay.getContext('2d');
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function hexToRgb01(h) {
    const n = parseInt(h.slice(1), 16);
    return [((n>>16)&255)/255, ((n>>8)&255)/255, (n&255)/255];
  }
  const ACCENT_RGB = hexToRgb01(ACCENT_LIGHT).map(function(v){ return Math.round(v*255); });

  // --- WebGL setup -------------------------------------------------------------------------
  const gl = glCanvas.getContext('webgl', { alpha: true, premultipliedAlpha: false })
          || glCanvas.getContext('experimental-webgl', { alpha: true });

  if (!gl) {
    render2DFallback();
    return;
  }

  const VERT_SRC = [
    'attribute vec2 a_pos;',
    'void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }'
  ].join('\n');

  const FRAG_SRC = [
    'precision highp float;',
    'uniform vec2 u_resolution;',
    'uniform float u_lon0;',
    'uniform float u_lat0;',
    'uniform float u_sunLon;',
    'uniform float u_globeRadius;',
    'uniform sampler2D u_dayTex;',
    'uniform sampler2D u_nightTex;',
    'uniform vec3 u_rimColor;',
    'const float PI = 3.14159265359;',
    'void main() {',
    '  vec2 uv = (gl_FragCoord.xy - 0.5*u_resolution) / (0.5*min(u_resolution.x, u_resolution.y));',
    '  float dist = length(uv) / u_globeRadius;',
    '  if (dist > 1.18) { discard; }',
    '  if (dist > 1.0) {',
    '    float rim = smoothstep(1.18, 1.0, dist);',
    '    gl_FragColor = vec4(u_rimColor, rim * 0.45);',
    '    return;',
    '  }',
    '  float x2 = uv.x / u_globeRadius;',
    '  float y2 = uv.y / u_globeRadius;',
    '  float z2 = sqrt(max(0.0, 1.0 - x2*x2 - y2*y2));',
    '  float cLat = cos(u_lat0); float sLat = sin(u_lat0);',
    '  float z1 = z2*cLat - y2*sLat;',
    '  float y1 = z2*sLat + y2*cLat;',
    '  float x1 = x2;',
    '  float cLon = cos(u_lon0); float sLon = sin(u_lon0);',
    '  float xw = x1*cLon + z1*sLon;',
    '  float zw = -x1*sLon + z1*cLon;',
    '  float yw = y1;',
    '  float lat = asin(clamp(yw, -1.0, 1.0));',
    '  float lon = atan(xw, zw);',
    // v=0.5+lat/PI (not "-lat/PI"): UNPACK_FLIP_Y_WEBGL=true already makes v=0 sample the
    // source image's top row, so this must not ALSO flip lat, or north/south swap (Europe
    // rendered as Antarctica without this — caught via screenshot during development).
    '  vec2 texUV = vec2(0.5 + lon/(2.0*PI), 0.5 + lat/PI);',
    '  vec3 dayColor = texture2D(u_dayTex, texUV).rgb;',
    '  vec3 nightColor = texture2D(u_nightTex, texUV).rgb;',
    '  vec3 sunDir = vec3(sin(u_sunLon), 0.0, cos(u_sunLon));',
    '  vec3 normal = normalize(vec3(xw, yw, zw));',
    '  float litFactor = dot(normal, sunDir);',
    '  float dayAmount = smoothstep(-0.15, 0.15, litFactor);',
    '  vec3 color = mix(nightColor, dayColor, dayAmount);',
    '  float limb = smoothstep(0.0, 1.0, z2);',
    '  color *= (0.78 + 0.22*limb);',
    '  gl_FragColor = vec4(color, 1.0);',
    '}'
  ].join('\n');

  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error('Shader compile error:', gl.getShaderInfoLog(s));
    }
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT_SRC));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG_SRC));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  const posBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, 'a_pos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  const uRes = gl.getUniformLocation(prog, 'u_resolution');
  const uLon0 = gl.getUniformLocation(prog, 'u_lon0');
  const uLat0 = gl.getUniformLocation(prog, 'u_lat0');
  const uSunLon = gl.getUniformLocation(prog, 'u_sunLon');
  const uGlobeRadius = gl.getUniformLocation(prog, 'u_globeRadius');
  const uDayTex = gl.getUniformLocation(prog, 'u_dayTex');
  const uNightTex = gl.getUniformLocation(prog, 'u_nightTex');
  const uRimColor = gl.getUniformLocation(prog, 'u_rimColor');

  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

  function makeTexture() {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
                  new Uint8Array([10, 12, 18, 255]));
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    return tex;
  }
  const dayTex = makeTexture();
  const nightTex = makeTexture();

  let texturesReady = 0;
  function loadTexture(tex, url, onReady) {
    const img = new Image();
    img.onload = function() {
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      onReady();
      requestDraw();
    };
    img.onerror = function() { render2DFallback(); };
    img.src = url;
  }
  loadTexture(dayTex, DAY_URL, function() { texturesReady++; });
  loadTexture(nightTex, NIGHT_URL, function() { texturesReady++; });

  let W = 0, H = 0, dpr = 1;
  function resize() {
    dpr = window.devicePixelRatio || 1;
    W = wrap.clientWidth; H = wrap.clientHeight;
    glCanvas.width = Math.round(W * dpr); glCanvas.height = Math.round(H * dpr);
    overlay.width = Math.round(W * dpr); overlay.height = Math.round(H * dpr);
    octx.setTransform(dpr, 0, 0, dpr, 0, 0);
    gl.viewport(0, 0, glCanvas.width, glCanvas.height);
    landedRadius = computeLandedRadius();
    draw();
  }

  let progress = 0;    // 0-1, live scroll position — drives day/night bidirectionally
  let maxProgress = 0; // high-water mark of progress — drives zoom/rotation, never decreases

  // Idle auto-spin: runs only until the first scroll, then freezes so the scroll-driven sweep
  // continues from exactly where it left off (no visual jump at the handoff).
  let idling = !reduceMotion;
  let spinBase = 0;     // radians, grows while idling
  let frozenOffset = 0; // spinBase (normalized to (-PI,PI]) captured at the moment idling ends
  function normalizeAngle(a) { return Math.atan2(Math.sin(a), Math.cos(a)); }

  function ease(t) { return t*t*(3 - 2*t); } // smoothstep, matches hero_map.py's easing

  function zoomT() { return Math.min(1, maxProgress / ZOOM_PHASE_END); }
  function nightT() {
    return Math.max(0, Math.min(1, (progress - ZOOM_PHASE_END) / (1 - ZOOM_PHASE_END)));
  }

  function lon0() {
    if (idling) return CENTER_LON + spinBase;
    // Sweeps from wherever idle spin froze back to exactly CENTER_LON as zoomT goes 0->1, so the
    // globe always lands dead-centered on Europe regardless of the idle spin's starting angle.
    const offset = frozenOffset * (1 - ease(zoomT()));
    return CENTER_LON + offset;
  }
  function sunLon() { return CENTER_LON + nightT() * Math.PI; } // noon over Europe -> midnight
  function globeRadius() { return ZOOM_OUT_RADIUS + (landedRadius - ZOOM_OUT_RADIUS) * ease(zoomT()); }

  // Forward view-space transform (mirrors the shader's inverse), used to place city markers and
  // (with an explicit L0) to solve for the landed zoom that matches hero_map.py's framing.
  function toView(lonDeg, latDeg, L0) {
    const lon = lonDeg * Math.PI / 180, lat = latDeg * Math.PI / 180;
    const x = Math.cos(lat) * Math.sin(lon), y = Math.sin(lat), z = Math.cos(lat) * Math.cos(lon);
    if (L0 === undefined) L0 = lon0();
    const B0 = CENTER_LAT;
    const x1 = x*Math.cos(L0) - z*Math.sin(L0);
    const z1 = x*Math.sin(L0) + z*Math.cos(L0);
    const y1 = y;
    const y2 = -z1*Math.sin(B0) + y1*Math.cos(B0);
    const z2 = z1*Math.cos(B0) + y1*Math.sin(B0);
    const x2 = x1;
    return { x: x2, y: y2, z: z2 };
  }

  // Solve for the GLOBE_RADIUS fraction at which the LAT_TOP..LAT_BOTTOM band (centered on
  // CENTER_LON, viewed head-on) fills the full viewport height — matching hero_map.py's crop.
  function computeLandedRadius() {
    if (!H) return landedRadius;
    const top = toView(CENTER_LON_DEG, LAT_TOP, CENTER_LON);
    const bot = toView(CENTER_LON_DEG, LAT_BOTTOM, CENTER_LON);
    const dy = top.y - bot.y;
    if (dy <= 0) return landedRadius;
    const rpxNeeded = H / dy;
    return rpxNeeded / (Math.min(W, H) / 2);
  }

  function drawOverlay() {
    octx.clearRect(0, 0, W, H);
    const Rpx = globeRadius() * Math.min(W, H) / 2;
    const pulse = reduceMotion ? 1 : (0.85 + 0.15*Math.sin(Date.now()/650));
    octx.textBaseline = 'middle';
    octx.font = '600 12px Inter, system-ui, sans-serif';
    for (const c of CITIES) {
      const v = toView(c.lon, c.lat);
      if (v.z <= 0.02) continue; // on the far side of the globe
      const sx = W/2 + v.x * Rpx, sy = H/2 - v.y * Rpx;
      const glow = Math.min(1, v.z * 1.3); // brighter near centre of the visible disc
      const r = (9 + 14*glow) * pulse;
      const rg = octx.createRadialGradient(sx, sy, 0, sx, sy, r);
      rg.addColorStop(0, 'rgba(' + ACCENT_RGB[0] + ',' + ACCENT_RGB[1] + ',' + ACCENT_RGB[2] + ',' + (0.5*glow) + ')');
      rg.addColorStop(1, 'rgba(' + ACCENT_RGB[0] + ',' + ACCENT_RGB[1] + ',' + ACCENT_RGB[2] + ',0)');
      octx.fillStyle = rg;
      octx.beginPath(); octx.arc(sx, sy, r, 0, Math.PI*2); octx.fill();
      octx.beginPath(); octx.arc(sx, sy, 3.2, 0, Math.PI*2);
      octx.fillStyle = '#FFF3E4';
      octx.fill();
      octx.fillStyle = 'rgba(242,166,90,0.9)';
      octx.fillText(c.name, sx + 8, sy);
    }
  }

  function draw() {
    if (!W) return;
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(prog);
    gl.uniform2f(uRes, glCanvas.width, glCanvas.height);
    gl.uniform1f(uLon0, lon0());
    gl.uniform1f(uLat0, CENTER_LAT);
    gl.uniform1f(uSunLon, sunLon());
    gl.uniform1f(uGlobeRadius, globeRadius());
    gl.uniform3f(uRimColor, ACCENT_RGB[0]/255, ACCENT_RGB[1]/255, ACCENT_RGB[2]/255);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, dayTex); gl.uniform1i(uDayTex, 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, nightTex); gl.uniform1i(uNightTex, 1);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    drawOverlay();
  }

  let raf = null;
  function requestDraw() { if (raf) return; raf = requestAnimationFrame(function() { raf = null; draw(); }); }

  function updateHint() {
    if (!hint) return;
    if (maxProgress < ZOOM_PHASE_END) {
      hint.textContent = 'Scroll ↓  zoom into Europe';
      hint.style.opacity = String(Math.max(0.35, 0.85 - zoomT()*0.5));
    } else {
      hint.textContent = 'Scroll ↓  day to night';
      hint.style.opacity = String(Math.max(0, 0.85 - nightT()*1.3));
    }
  }

  function onScroll() {
    const max = wrap.scrollHeight - wrap.clientHeight;
    progress = max > 0 ? Math.min(1, Math.max(0, wrap.scrollTop / max)) : 0;
    if (progress > 0 && idling) {
      idling = false;
      frozenOffset = normalizeAngle(spinBase);
    }
    maxProgress = Math.max(maxProgress, progress);
    updateHint();
    requestDraw();
  }

  window.addEventListener('resize', resize);
  wrap.addEventListener('scroll', onScroll, { passive: true });

  if (reduceMotion) { progress = 1; maxProgress = 1; idling = false; }
  resize();
  updateHint();
  if (!reduceMotion) {
    setInterval(function() { if (progress > 0.1) requestDraw(); }, 90);
    // Idle auto-spin, time-based (not scroll-driven) — freezes itself the moment onScroll sees
    // the first nonzero progress (see `idling` above).
    let lastT = null;
    function idleTick(ts) {
      if (!idling) return;
      if (lastT !== null) {
        spinBase += (ts - lastT) / 1000 * (2*Math.PI / 40); // one full rotation per ~40s
      }
      lastT = ts;
      requestDraw();
      requestAnimationFrame(idleTick);
    }
    requestAnimationFrame(idleTick);
  }

  // --- Fallback: no WebGL -> flat vector silhouette, never render blank --------------------
  function render2DFallback() {
    glCanvas.style.display = 'none';
    const ctx = overlay.getContext('2d');
    function mercX(lon) { return lon * Math.PI/180; }
    function mercY(lat) { return Math.log(Math.tan(Math.PI/4 + (lat*Math.PI/180)/2)); }
    function resizeFallback() {
      const dpr2 = window.devicePixelRatio || 1;
      const w = wrap.clientWidth, h = wrap.clientHeight;
      overlay.width = Math.round(w*dpr2); overlay.height = Math.round(h*dpr2);
      ctx.setTransform(dpr2, 0, 0, dpr2, 0, 0);
      const yTop = mercY(55.5), yBot = mercY(37.5);
      const s = h / (yTop - yBot);
      const cx = mercX(8.5);
      ctx.fillStyle = '#0B0E14'; ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#161B26'; ctx.strokeStyle = '#2E3646'; ctx.lineWidth = 0.7;
      function proj(lon, lat) { return [ w/2 + (mercX(lon)-cx)*s, (yTop-mercY(lat))*s ]; }
      function poly(rings) {
        for (const ring of rings) {
          ctx.beginPath();
          for (let i=0;i<ring.length;i++) { const p = proj(ring[i][0], ring[i][1]); if (i===0) ctx.moveTo(p[0],p[1]); else ctx.lineTo(p[0],p[1]); }
          ctx.closePath(); ctx.fill(); ctx.stroke();
        }
      }
      for (const g of GEO.geometries) {
        if (g.type === 'Polygon') poly(g.coordinates);
        else if (g.type === 'MultiPolygon') for (const p2 of g.coordinates) poly(p2);
      }
      ctx.fillStyle = '#F2A65A';
      for (const c of CITIES) { const p = proj(c.lon, c.lat); ctx.beginPath(); ctx.arc(p[0], p[1], 3, 0, Math.PI*2); ctx.fill(); }
    }
    window.addEventListener('resize', resizeFallback);
    resizeFallback();
  }
})();
</script>
"""
