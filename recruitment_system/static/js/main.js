// ============================================================
// Neural node-network ambient background
// Echoes the attention-graph idea behind BERT — nodes connect
// to their nearest neighbours and drift slowly.
// ============================================================
(function nodeNetwork() {
  const canvas = document.getElementById("node-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h, nodes;
  const NODE_COUNT_BASE = 60;
  const LINK_DIST = 130;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function initNodes() {
    const count = Math.min(NODE_COUNT_BASE, Math.floor((w * h) / 22000));
    nodes = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 1.6 + 0.6,
    }));
  }

  function step() {
    ctx.clearRect(0, 0, w, h);
    for (const n of nodes) {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > w) n.vx *= -1;
      if (n.y < 0 || n.y > h) n.vy *= -1;
    }
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < LINK_DIST) {
          ctx.strokeStyle = `rgba(124,140,255,${0.14 * (1 - dist / LINK_DIST)})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }
    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(160,175,255,0.55)";
      ctx.fill();
    }
    requestAnimationFrame(step);
  }

  window.addEventListener("resize", () => { resize(); initNodes(); });
  resize();
  initNodes();
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    requestAnimationFrame(step);
  }
})();

// ============================================================
// Scroll reveal
// ============================================================
(function scrollReveal() {
  const els = document.querySelectorAll(".reveal");
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("in-view"); });
  }, { threshold: 0.12 });
  els.forEach((el) => io.observe(el));
})();

// ============================================================
// Auto-dismiss flash messages
// ============================================================
(function flashDismiss() {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => { el.style.transition = "opacity .5s ease"; el.style.opacity = "0"; setTimeout(() => el.remove(), 500); }, 5000);
  });
})();

// ============================================================
// Score ring animator — call from a page with data-score attr
// ============================================================
function animateScoreRing(el) {
  const score = parseFloat(el.dataset.score || "0");
  const circle = el.querySelector(".score-ring-fg");
  const numEl = el.querySelector(".num");
  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;
  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  circle.style.strokeDashoffset = circumference;

  requestAnimationFrame(() => {
    const offset = circumference - (score / 100) * circumference;
    circle.style.strokeDashoffset = offset;
  });

  let current = 0;
  const duration = 1200;
  const start = performance.now();
  function tick(now) {
    const p = Math.min(1, (now - start) / duration);
    current = Math.floor(p * score);
    numEl.textContent = current;
    if (p < 1) requestAnimationFrame(tick);
    else numEl.textContent = score;
  }
  requestAnimationFrame(tick);
}

document.querySelectorAll("[data-score-ring]").forEach(animateScoreRing);

// ============================================================
// Progress bars animator
// ============================================================
document.querySelectorAll("[data-bar-fill]").forEach((el) => {
  const val = parseFloat(el.dataset.barFill || "0");
  requestAnimationFrame(() => { el.style.width = val + "%"; });
});

// ============================================================
// Dropzone (resume upload) interactivity
// ============================================================
(function dropzone() {
  const dz = document.querySelector(".dropzone");
  if (!dz) return;
  const input = dz.querySelector("input[type=file]");
  const label = dz.querySelector(".dz-filename");

  function showFile(name) {
    dz.classList.add("scanning");
    if (label) label.textContent = name;
    setTimeout(() => dz.classList.remove("scanning"), 1800);
  }

  dz.addEventListener("click", () => input.click());
  input.addEventListener("change", () => { if (input.files[0]) showFile(input.files[0].name); });

  ["dragover", "dragleave", "drop"].forEach((evt) => {
    dz.addEventListener(evt, (e) => {
      e.preventDefault();
      if (evt === "dragover") dz.classList.add("drag");
      else dz.classList.remove("drag");
      if (evt === "drop" && e.dataTransfer.files[0]) {
        input.files = e.dataTransfer.files;
        showFile(e.dataTransfer.files[0].name);
      }
    });
  });
})();

// ============================================================
// Full-page loading overlay for form submits (resume parsing / ATS scoring)
// ============================================================
function showLoadingOverlay(text) {
  let overlay = document.getElementById("global-loading-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "global-loading-overlay";
    overlay.className = "loading-overlay";
    overlay.innerHTML = `<div class="scan-orb"></div><div class="loading-text">${text || "Processing..."}</div>`;
    document.body.appendChild(overlay);
  }
  overlay.classList.remove("hidden");
}

document.querySelectorAll("form[data-loading-text]").forEach((form) => {
  form.addEventListener("submit", () => showLoadingOverlay(form.dataset.loadingText));
});
