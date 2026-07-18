// ==================================================
// Hamid Ali Awan — Portfolio (Vanilla JS)
// ==================================================

// ---------- Typing effect ----------
(function () {
  const el = document.getElementById("typed");
  if (!el) return;
  const phrases = ["Machine Learning Specialist", "Backend Developer"];
  let pi = 0, ci = 0, deleting = false;
  function tick() {
    const phrase = phrases[pi];
    if (!deleting) {
      ci++;
      el.textContent = phrase.slice(0, ci);
      if (ci === phrase.length) { deleting = true; return setTimeout(tick, 1600); }
    } else {
      ci--;
      el.textContent = phrase.slice(0, ci);
      if (ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; }
    }
    setTimeout(tick, deleting ? 40 : 75);
  }
  setTimeout(tick, 300);
})();

// ---------- Scroll reveal ----------
(function () {
  const els = document.querySelectorAll(".reveal");
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("in");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  els.forEach((el, i) => {
    el.style.transitionDelay = `${(i % 6) * 90}ms`;
    io.observe(el);
  });
})();

// ---------- Nav scroll state ----------
(function () {
  const nav = document.getElementById("nav");
  if (!nav) return;
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 20);
  window.addEventListener("scroll", onScroll);
  onScroll();
})();

// ---------- Mobile menu ----------
(function () {
  const btn = document.getElementById("menuBtn");
  const menu = document.getElementById("mobileMenu");
  if (!btn || !menu) return;
  btn.addEventListener("click", () => menu.classList.toggle("open"));
  menu.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => menu.classList.remove("open")));
})();

// ---------- Theme toggle ----------
(function () {
  const root = document.documentElement;
  const btn = document.getElementById("themeToggle");
  const thumb = document.getElementById("themeThumb");
  if (!btn) return;

  const saved = localStorage.getItem("theme");
  const initial = saved === "light" ? "light" : "dark";
  applyTheme(initial);

  btn.addEventListener("click", () => {
    const next = root.classList.contains("dark") ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem("theme", next);
  });

  function applyTheme(t) {
    root.classList.remove("dark", "light");
    root.classList.add(t);
    if (thumb) {
      thumb.classList.toggle("left", t === "dark");
      thumb.classList.toggle("right", t === "light");
    }
  }
})();

// ---------- Contact form ----------
(function () {
  const form = document.getElementById("contactForm");
  const status = document.getElementById("formStatus");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.className = "form-status";
    status.textContent = "Sending...";
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      const res = await fetch("/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      if (res.ok && json.ok) {
        status.className = "form-status ok";
        status.textContent = json.message || "Message sent!";
        form.reset();
      } else {
        status.className = "form-status err";
        status.textContent = json.error || "Something went wrong.";
      }
    } catch (err) {
      status.className = "form-status err";
      status.textContent = "Network error. Please try again.";
    }
  });
})();
