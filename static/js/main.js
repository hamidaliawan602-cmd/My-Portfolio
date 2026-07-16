// Navbar scroll effect
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 50);
});

// Hamburger menu
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');
hamburger.addEventListener('click', () => {
  navLinks.classList.toggle('active');
  hamburger.classList.toggle('open');
});
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => navLinks.classList.remove('active'));
});

// Active nav link on scroll
const sections = document.querySelectorAll('section[id]');
window.addEventListener('scroll', () => {
  const scrollY = window.scrollY + 100;
  sections.forEach(sec => {
    const top = sec.offsetTop - 100;
    const height = sec.offsetHeight;
    const id = sec.getAttribute('id');
    const link = document.querySelector(`.nav-links a[href="#${id}"]`);
    if (link) {
      if (scrollY >= top && scrollY < top + height) {
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
        link.classList.add('active');
      }
    }
  });
});

// Typing effect
const typed = document.querySelector('.typed');
const words = ['ML Engineer', 'Web Developer', 'Python Developer', 'Problem Solver'];
let wordIndex = 0, charIndex = 0, isDeleting = false;
function typeEffect() {
  const current = words[wordIndex];
  typed.textContent = isDeleting ? current.substring(0, charIndex--) : current.substring(0, charIndex++);
  if (!isDeleting && charIndex > current.length) {
    setTimeout(() => { isDeleting = true; typeEffect(); }, 1800);
    return;
  }
  if (isDeleting && charIndex < 0) {
    isDeleting = false;
    wordIndex = (wordIndex + 1) % words.length;
  }
  setTimeout(typeEffect, isDeleting ? 40 : 100);
}
typeEffect();

// Scroll reveal
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: 0.15 });
document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));

// Contact form
document.getElementById('contactForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const status = document.getElementById('formStatus');
  const formData = {
    name: e.target.name.value,
    email: e.target.email.value,
    subject: e.target.subject.value,
    message: e.target.message.value
  };
  try {
    const res = await fetch('/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    const data = await res.json();
    status.textContent = data.message;
    status.className = 'form-status success';
    e.target.reset();
  } catch (err) {
    status.textContent = 'Something went wrong. Please try again.';
    status.className = 'form-status error';
  }
});
