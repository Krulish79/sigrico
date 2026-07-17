/* SigriCo — interactions
   1) bioluminescent particle field in the hero
   2) scroll-reveal for .reveal elements
   3) nav background state on scroll                                    */

(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 1. NAV state ---------- */
  const nav = document.getElementById("nav");
  const onScroll = () => {
    if (window.scrollY > 40) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- 2. Scroll reveal ---------- */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
  }

  /* ---------- Interlude videos: play only while on-screen ---------- */
  const ilVideos = document.querySelectorAll(".interlude__video");
  ilVideos.forEach((v) => { v.muted = true; });   // required for autoplay
  if (ilVideos.length && !reduceMotion && "IntersectionObserver" in window) {
    const vio = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.play().catch(() => {});
          else e.target.pause();
        });
      },
      { threshold: 0.25 }
    );
    ilVideos.forEach((v) => vio.observe(v));
  }
  // reduced motion → leave paused; the poster frame shows.

  /* ---------- Contact form: submit inline, never leave the page ---------- */
  const form = document.getElementById("contactForm");
  if (form) {
    const statusEl = document.getElementById("cf-status");
    const doneEl = document.getElementById("contactDone");
    const btn = document.getElementById("cf-submit");
    const setStatus = (msg, kind) => {
      statusEl.textContent = msg;
      statusEl.className = "cform__status" + (kind ? " " + kind : "");
    };

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }

      // Not connected yet? Fail loudly here instead of pinging a fake inbox.
      if (form.action.indexOf("YOUR_EMAIL") !== -1) {
        setStatus("Form isn't connected yet — set your email in the form action (index.html).", "err");
        return;
      }

      btn.disabled = true;
      setStatus("Sending…", "");
      // FormSubmit's JSON endpoint keeps it inline (no redirect).
      const endpoint = form.action.replace("formsubmit.co/", "formsubmit.co/ajax/");
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { Accept: "application/json" },
          body: new FormData(form),
        });
        if (res.ok) {
          form.hidden = true;
          doneEl.hidden = false;
          doneEl.classList.add("in");
          doneEl.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {
          setStatus("Something went wrong — please try again in a moment.", "err");
          btn.disabled = false;
        }
      } catch (err) {
        setStatus("Network error — please check your connection and try again.", "err");
        btn.disabled = false;
      }
    });
  }

  /* ---------- 3. Bioluminescent particle field ---------- */
  const canvas = document.getElementById("particles");
  const rays = document.querySelector(".rays");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let W, H, motes, orbs, beams, raf, t = 0;
  void rays; // rays keeps its CSS ambient wash; canvas now draws the volumetric shafts
  const COLORS = ["42,185,198", "22,164,176", "237,242,248"]; // aqua / teal / ice — bubbles read blue-white

  // pointer parallax (eased)
  const mouse = { x: 0.5, y: 0.5 };
  const par = { x: 0, y: 0 };

  function size() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth;
    H = canvas.clientHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function seed() {
    // rising bubbles
    const count = Math.min(Math.round((W * H) / 34000), 74);
    motes = Array.from({ length: count }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 4.5 + 1.6,           // bubbles, varied sizes
      vy: -(Math.random() * 0.34 + 0.10),      // rise steadily
      wob: Math.random() * Math.PI * 2,        // gentle side-to-side wobble
      wobS: Math.random() * 0.02 + 0.01,
      sway: Math.random() * 0.5 + 0.3,
      a: Math.random() * 0.35 + 0.22,          // translucent, no twinkle
      depth: Math.random() * 0.7 + 0.3,           // parallax depth
      c: COLORS[Math.floor(Math.random() * COLORS.length)],
    }));
    // volumetric god-ray shafts descending from the surface through the water
    beams = Array.from({ length: 7 }, (_, i) => ({
      base: ((i + 0.5) / 7 - 0.5) * 0.9,       // fan ~±26° across the top
      w: 0.014 + Math.random() * 0.022,        // half-width — tighter, crisper shafts
      len: H * (1.15 + Math.random() * 0.4),   // reaches well down into the deep
      ph: Math.random() * Math.PI * 2,
      sp: 0.004 + Math.random() * 0.004,       // slow sway speed (per frame)
      amp: 0.03 + Math.random() * 0.05,        // sway amplitude (rad)
      a: 0.20 + Math.random() * 0.15,          // base brightness (more pronounced)
      c: i % 4 === 1 ? "22,164,176" : "42,185,198",   // all-blue shafts (two blue tones)
    }));
    // a few large soft bioluminescent bloom orbs
    orbs = Array.from({ length: 5 }, (_, i) => ({
      x: Math.random() * W,
      y: Math.random() * H * 0.9,
      r: Math.random() * 130 + 100,
      vy: -(Math.random() * 0.12 + 0.03),
      vx: (Math.random() - 0.5) * 0.06,
      tw: Math.random() * Math.PI * 2,
      depth: Math.random() * 0.5 + 0.15,
      c: i % 3 === 0 ? COLORS[2] : COLORS[Math.floor(Math.random() * 2)],
    }));
  }

  function drawScene() {
    // ease parallax toward pointer
    par.x += ((mouse.x - 0.5) * 40 - par.x) * 0.05;
    par.y += ((mouse.y - 0.5) * 26 - par.y) * 0.05;

    ctx.clearRect(0, 0, W, H);
    ctx.globalCompositeOperation = "lighter"; // additive glow = bioluminescence
    t++;

    // god-ray shafts — soft volumetric light drifting down through the water
    ctx.save();
    ctx.filter = "blur(11px)";
    const ax = W * 0.5 + par.x * 0.4;  // apex, above the top edge, drifts with pointer
    const ay = -H * 0.12;
    for (const b of beams) {
      const ang = b.base + Math.sin(t * b.sp + b.ph) * b.amp;
      const a1 = ang - b.w, a2 = ang + b.w;
      const mx = ax + Math.sin(ang) * b.len, my = ay + Math.cos(ang) * b.len;
      const alpha = b.a * (0.55 + 0.45 * Math.sin(t * b.sp * 1.7 + b.ph)); // shimmer
      const g = ctx.createLinearGradient(ax, ay, mx, my);
      g.addColorStop(0, `rgba(${b.c},${alpha})`);
      g.addColorStop(0.5, `rgba(${b.c},${alpha * 0.5})`);
      g.addColorStop(1, `rgba(${b.c},0)`);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax + Math.sin(a1) * b.len, ay + Math.cos(a1) * b.len);
      ctx.lineTo(ax + Math.sin(a2) * b.len, ay + Math.cos(a2) * b.len);
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore(); // drop the blur filter (composite stays "lighter")

    // bloom orbs
    for (const o of orbs) {
      o.y += o.vy; o.x += o.vx; o.tw += 0.006;
      if (o.y < -o.r) { o.y = H + o.r; o.x = Math.random() * W; }
      const glow = 0.07 + 0.06 * (0.5 + 0.5 * Math.sin(o.tw));
      const ox = o.x + par.x * o.depth, oy = o.y + par.y * o.depth;
      const g = ctx.createRadialGradient(ox, oy, 0, ox, oy, o.r);
      g.addColorStop(0, `rgba(${o.c},${glow})`);
      g.addColorStop(1, `rgba(${o.c},0)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(ox, oy, o.r, 0, Math.PI * 2); ctx.fill();
    }

    // rising bubbles (translucent ring + soft rim + specular highlight)
    ctx.globalCompositeOperation = "screen";   // luminous but soft, not star-hot
    ctx.shadowBlur = 0;
    for (const p of motes) {
      p.y += p.vy;
      p.wob += p.wobS;
      if (p.y < -14) { p.y = H + 14; p.x = Math.random() * W; }
      const px = p.x + Math.sin(p.wob) * p.sway + par.x * p.depth;
      const py = p.y + par.y * p.depth;

      // faint translucent body
      ctx.beginPath();
      ctx.arc(px, py, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.c},${p.a * 0.14})`;
      ctx.fill();
      // rim
      ctx.lineWidth = Math.max(0.6, p.r * 0.16);
      ctx.strokeStyle = `rgba(${p.c},${p.a})`;
      ctx.stroke();
      // specular highlight (upper-left)
      ctx.beginPath();
      ctx.arc(px - p.r * 0.34, py - p.r * 0.34, Math.max(0.5, p.r * 0.2), 0, Math.PI * 2);
      ctx.fillStyle = `rgba(237,242,248,${p.a * 0.85})`;
      ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
  }

  function frame() { drawScene(); raf = requestAnimationFrame(frame); }
  function init() { size(); seed(); }
  init();

  // Reduced motion: render ONE static frame so the light shafts still show,
  // just without the drift and shimmer. Full animation otherwise.
  if (reduceMotion) {
    drawScene();
  } else {
    frame();

    // pointer parallax (eased in drawScene)
    window.addEventListener("pointermove", (e) => {
      mouse.x = e.clientX / window.innerWidth;
      mouse.y = e.clientY / window.innerHeight;
    }, { passive: true });

    // pause the loop when the hero scrolls out of view (save cycles)
    const hero = document.getElementById("top");
    if ("IntersectionObserver" in window) {
      new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) { if (!raf) frame(); }
          else { cancelAnimationFrame(raf); raf = null; }
        });
      }, { threshold: 0 }).observe(hero);
    }
  }

  let rt;
  window.addEventListener("resize", () => {
    clearTimeout(rt);
    rt = setTimeout(() => { init(); if (reduceMotion) drawScene(); }, 150);
  });
})();
