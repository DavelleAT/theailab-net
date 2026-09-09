// Decorative full-page background flourish (homepage only). A sunburst of
// thin rays radiating from a point that eases toward the cursor and slowly
// rotates with scroll position. Each ray animates independently — its own
// length "breathes" and its own color flows through the site's palette on
// its own phase offset — rather than the whole canvas moving/coloring as
// one rigid unit. Purely decorative — no functional purpose, disabled
// entirely when the visitor's OS has "reduce motion" turned on.
(function () {
  var canvas = document.getElementById("bg-flourish");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var LIGHT_PALETTE = [
    [63, 155, 142], [95, 168, 158], [110, 145, 155],
    [75, 180, 165], [120, 160, 170], [85, 175, 160]
  ];
  var DARK_PALETTE = [
    [93, 181, 163], [108, 200, 185], [140, 190, 175],
    [115, 210, 190], [160, 195, 185], [125, 215, 200]
  ];

  var W, H, DPR;
  function resize() {
    DPR = window.devicePixelRatio || 1;
    W = window.innerWidth;
    H = window.innerHeight * 1.5;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }

  var RAY_COUNT = 150;
  var rays = [];
  for (var i = 0; i < RAY_COUNT; i++) {
    rays.push({
      angle: Math.random() * Math.PI * 2,
      baseLength: 200 + Math.random() * 650,
      pulseAmp: 30 + Math.random() * 90,
      pulseSpeed: 0.15 + Math.random() * 0.35,
      pulsePhase: Math.random() * Math.PI * 2,
      colorPhase: Math.random() * 10,
      colorSpeed: 0.04 + Math.random() * 0.08,
      width: 0.5 + Math.random() * 1.1,
      dotR: 1 + Math.random() * 2.4
    });
  }

  var BG_LIGHT = "#faf8f3";
  var BG_DARK = "#0f1515";

  function isDark() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function currentPalette() {
    return isDark() ? DARK_PALETTE : LIGHT_PALETTE;
  }

  // Smoothly interpolate around the palette (wrapping) at position `p`
  // (any real number — integer part selects the pair, fraction blends).
  function paletteColor(palette, p) {
    var n = palette.length;
    var i0 = ((Math.floor(p) % n) + n) % n;
    var i1 = (i0 + 1) % n;
    var t = p - Math.floor(p);
    var c0 = palette[i0], c1 = palette[i1];
    var r = c0[0] + (c1[0] - c0[0]) * t;
    var g = c0[1] + (c1[1] - c0[1]) * t;
    var b = c0[2] + (c1[2] - c0[2]) * t;
    return "rgb(" + (r | 0) + "," + (g | 0) + "," + (b | 0) + ")";
  }

  var targetX = 0, targetY = 0, curX = 0, curY = 0, rotation = 0;

  function draw(t) {
    // Solid fill matching the site's own --bg exactly, not clearRect — a
    // fully transparent canvas lets the browser's own default page-background
    // color-scheme show through in the gaps between rays (pure white in
    // light mode, which reads as flatter/whiter than the site's actual warm
    // off-white; near-black in dark mode, which happens to look fine by
    // coincidence). This keeps the base color exactly right everywhere
    // without a gradient or edge — no seam, just always the correct color.
    ctx.fillStyle = isDark() ? BG_DARK : BG_LIGHT;
    ctx.fillRect(0, 0, W, H);
    var cx = W / 2 + curX;
    var cy = H / 2 + curY;
    var palette = currentPalette();

    ctx.lineCap = "round";
    for (var i = 0; i < rays.length; i++) {
      var r = rays[i];
      var a = r.angle + rotation;
      var length = r.baseLength + Math.sin(t * r.pulseSpeed + r.pulsePhase) * r.pulseAmp;
      var x2 = cx + Math.cos(a) * length;
      var y2 = cy + Math.sin(a) * length;
      var color = paletteColor(palette, t * r.colorSpeed + r.colorPhase);
      var twinkle = 0.55 + 0.45 * Math.sin(t * r.pulseSpeed * 1.7 + r.colorPhase);

      ctx.globalAlpha = 0.28 * twinkle;
      ctx.strokeStyle = color;
      ctx.lineWidth = r.width;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      ctx.globalAlpha = 0.7 * twinkle + 0.15;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x2, y2, r.dotR, 0, Math.PI * 2);
      ctx.fill();
    }

    var glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, 70);
    glow.addColorStop(0, paletteColor(palette, t * 0.06));
    glow.addColorStop(1, "transparent");
    ctx.globalAlpha = 0.45;
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(cx, cy, 70, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  resize();

  if (reduceMotion) {
    draw(0);
    window.addEventListener("resize", function () { resize(); draw(0); });
    return;
  }

  window.addEventListener("resize", resize);
  window.addEventListener("mousemove", function (e) {
    targetX = (e.clientX - W / 2) * 0.15;
    targetY = (e.clientY - H / 2) * 0.15;
  });
  window.addEventListener("scroll", function () {
    rotation = (window.scrollY || 0) * 0.05 * Math.PI / 180;
  }, { passive: true });

  // Clicking empty background reshuffles every ray's shape and jumps its
  // color forward, like a new burst. The canvas itself sits at z-index:-1
  // (so it stays visually behind everything), which means normal in-flow
  // content always wins the hit-test over it per CSS stacking rules — so
  // this listens on the document instead and reshuffles unless the click
  // landed on/inside actual interactive content.
  document.addEventListener("click", function (e) {
    if (e.target.closest("a, button, .map-card, .news-card, .here-card, table")) return;
    for (var i = 0; i < rays.length; i++) {
      var r = rays[i];
      r.angle = Math.random() * Math.PI * 2;
      r.baseLength = 200 + Math.random() * 650;
      r.pulsePhase = Math.random() * Math.PI * 2;
      r.colorPhase += 1.5 + Math.random() * 2.5;
    }
  });

  function loop(ts) {
    curX += (targetX - curX) * 0.05;
    curY += (targetY - curY) * 0.05;
    draw(ts / 1000);
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();
