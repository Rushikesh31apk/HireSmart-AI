/* ═══════════════════════════════════════════════════════════════
   HireSmart AI — Main JavaScript
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── Navbar scroll effect ────────────────────────────────────────
const mainNav = document.getElementById('mainNav');
if (mainNav) {
  window.addEventListener('scroll', () => {
    mainNav.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// ── Scroll animations ───────────────────────────────────────────
const observerOpts = { threshold: 0.1, rootMargin: '0px 0px -40px 0px' };
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('visible'), i * 80);
      observer.unobserve(e.target);
    }
  });
}, observerOpts);

document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

// ── Counter animation ───────────────────────────────────────────
function animateCounter(el) {
  const target = parseFloat(el.dataset.target || el.textContent.replace(/[^0-9.]/g, ''));
  const suffix = el.dataset.suffix || '';
  const prefix = el.dataset.prefix || '';
  const isFloat = target % 1 !== 0;
  const duration = 2000;
  const step = 16;
  const increment = target / (duration / step);
  let current = 0;

  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    el.textContent = prefix + (isFloat ? current.toFixed(1) : Math.floor(current).toLocaleString()) + suffix;
  }, step);
}

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      animateCounter(e.target);
      counterObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('[data-counter]').forEach(el => counterObserver.observe(el));

// ── Auto-dismiss flash alerts ───────────────────────────────────
setTimeout(() => {
  document.querySelectorAll('.hs-alert').forEach(el => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    bsAlert.close();
  });
}, 5000);

// ── Password toggle ─────────────────────────────────────────────
document.querySelectorAll('.toggle-pass').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.closest('.input-icon-wrap').querySelector('input');
    const icon  = btn.querySelector('i');
    if (input.type === 'password') {
      input.type = 'text';
      icon.className = 'fa-solid fa-eye-slash';
    } else {
      input.type = 'password';
      icon.className = 'fa-solid fa-eye';
    }
  });
});

// ── OTP digit inputs ────────────────────────────────────────────
document.querySelectorAll('.otp-digit').forEach((digit, idx, all) => {
  digit.addEventListener('input', () => {
    digit.value = digit.value.replace(/\D/g, '').slice(0, 1);
    if (digit.value && idx < all.length - 1) all[idx + 1].focus();
    // Update hidden full OTP
    const otpFull = document.getElementById('otp_full');
    if (otpFull) otpFull.value = Array.from(all).map(d => d.value).join('');
  });
  digit.addEventListener('keydown', (e) => {
    if (e.key === 'Backspace' && !digit.value && idx > 0) all[idx - 1].focus();
  });
  digit.addEventListener('paste', (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    text.split('').forEach((ch, i) => { if (all[i]) all[i].value = ch; });
    const otpFull = document.getElementById('otp_full');
    if (otpFull) otpFull.value = text;
    all[Math.min(text.length, all.length - 1)].focus();
  });
});

// ── Resend OTP ──────────────────────────────────────────────────
const resendBtn = document.getElementById('resendOtpBtn');
if (resendBtn) {
  let cooldown = 60;
  const startCooldown = () => {
    resendBtn.disabled = true;
    const timer = setInterval(() => {
      cooldown--;
      resendBtn.textContent = `Resend OTP (${cooldown}s)`;
      if (cooldown <= 0) {
        clearInterval(timer);
        resendBtn.textContent = 'Resend OTP';
        resendBtn.disabled = false;
        cooldown = 60;
      }
    }, 1000);
  };
  resendBtn.addEventListener('click', async () => {
    try {
      const res  = await fetch('/resend-otp', { method: 'POST' });
      const data = await res.json();
      showToast(data.message, data.success ? 'success' : 'danger');
      if (data.success) startCooldown();
    } catch { showToast('Network error.', 'danger'); }
  });
}

// ── Toast helper ────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const wrapper = document.querySelector('.flash-wrapper') || createFlashWrapper();
  const div = document.createElement('div');
  div.className = `hs-alert alert-${type} alert-dismissible fade show`;
  div.role = 'alert';
  div.innerHTML = `<i class="fa-solid fa-circle-info me-2"></i>${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  wrapper.appendChild(div);
  setTimeout(() => { try { bootstrap.Alert.getOrCreateInstance(div).close(); } catch {} }, 5000);
}

function createFlashWrapper() {
  const d = document.createElement('div');
  d.className = 'flash-wrapper';
  document.body.appendChild(d);
  return d;
}

// ── Resume Form Wizard ──────────────────────────────────────────
const ResumeWizard = (() => {
  let currentStep = 0;
  const panels  = document.querySelectorAll('.form-panel');
  const wSteps  = document.querySelectorAll('.w-step');
  const resumeId = document.getElementById('resume_id')?.value;

  if (!panels.length) return;

  const goTo = (step) => {
    if (step < 0 || step >= panels.length) return;
    panels.forEach((p, i) => p.classList.toggle('active', i === step));
    wSteps.forEach((s, i) => {
      s.classList.remove('active', 'completed');
      if (i === step) s.classList.add('active');
      if (i < step)  s.classList.add('completed');
    });
    currentStep = step;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Navigation buttons
  document.querySelectorAll('[data-step-next]').forEach(btn => {
    btn.addEventListener('click', () => goTo(currentStep + 1));
  });
  document.querySelectorAll('[data-step-prev]').forEach(btn => {
    btn.addEventListener('click', () => goTo(currentStep - 1));
  });
  wSteps.forEach((s, i) => {
    s.addEventListener('click', () => goTo(i));
  });

  // Photo preview
  const photoInput = document.getElementById('photoInput');
  if (photoInput) {
    photoInput.addEventListener('change', () => {
      const file = photoInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = document.getElementById('photoPreview');
        if (img) img.src = e.target.result;
        document.getElementById('photoPlaceholder')?.classList.add('d-none');
        img?.classList.remove('d-none');
        // Store b64 in hidden field
        const hid = document.getElementById('photo_b64');
        if (hid) hid.value = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  // Dynamic items (education, projects, certs)
  document.querySelectorAll('[data-add-item]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target   = btn.dataset.addItem;
      const template = document.getElementById(`tpl_${target}`);
      const container = document.getElementById(`container_${target}`);
      if (template && container) {
        const clone = template.content.cloneNode(true);
        const idx   = container.children.length;
        // Update indices
        clone.querySelectorAll('[name]').forEach(el => {
          el.name = el.name.replace('__idx__', idx);
          el.id   = el.id?.replace('__idx__', idx) || el.id;
        });
        container.appendChild(clone);
        attachRemoveListeners(container);
      }
    });
  });

  function attachRemoveListeners(container) {
    container.querySelectorAll('.remove-item-btn').forEach(btn => {
      btn.onclick = () => btn.closest('.dynamic-item').remove();
    });
  }
  document.querySelectorAll('.dynamic-container').forEach(attachRemoveListeners);

  // Save form data
  const saveBtn = document.getElementById('saveBtn');
  const saveFinalBtn = document.getElementById('saveFinalBtn');

  const collectData = () => {
    const fd = {};
    // Personal
    ['full_name','role','phone','email','address','linkedin','github','about'].forEach(k => {
      const el = document.getElementById(k);
      if (el) fd[k] = el.value.trim();
    });
    // Photo
    const pb = document.getElementById('photo_b64');
    if (pb?.value) fd.photo_b64 = pb.value;

    // Skills
    fd.skills = {};
    ['languages','tools','databases','core'].forEach(k => {
      const el = document.getElementById(`skill_${k}`);
      if (el) fd.skills[k] = el.value.trim();
    });

    // Education
    fd.education = [];
    document.querySelectorAll('#container_education .dynamic-item').forEach((item, i) => {
      const get = (n) => item.querySelector(`[name="edu_${n}_${i}"]`)?.value.trim() || '';
      fd.education.push({ degree: get('degree'), school: get('school'), year: get('year'), gpa: get('gpa') });
    });

    // Projects
    fd.projects = [];
    document.querySelectorAll('#container_projects .dynamic-item').forEach((item, i) => {
      const get = (n) => item.querySelector(`[name="proj_${n}_${i}"]`)?.value.trim() || '';
      fd.projects.push({ name: get('name'), tech: get('tech'), description: get('desc'), link: get('link') });
    });

    // Certifications
    fd.certifications = [];
    document.querySelectorAll('#container_certifications .dynamic-item').forEach((item, i) => {
      const get = (n) => item.querySelector(`[name="cert_${n}_${i}"]`)?.value.trim() || '';
      fd.certifications.push({ name: get('name'), issuer: get('issuer'), year: get('year') });
    });

    // Text areas
    ['achievements','hobbies'].forEach(k => {
      const el = document.getElementById(k);
      if (el) fd[k] = el.value.trim();
    });

    const titleEl = document.getElementById('resume_title');
    return { title: titleEl?.value.trim() || 'My Resume', data: fd };
  };

  const doSave = async (redirectUrl) => {
    if (!resumeId) return;
    const payload = collectData();
    showSaveIndicator('Saving...');
    try {
      const res  = await fetch(`/resume/${resumeId}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      showSaveIndicator(data.success ? '✓ Saved!' : 'Error!');
      if (data.success && redirectUrl) {
        setTimeout(() => window.location.href = redirectUrl, 500);
      }
    } catch { showSaveIndicator('Error!'); }
  };

  if (saveBtn) saveBtn.addEventListener('click', () => doSave(null));
  if (saveFinalBtn) {
    saveFinalBtn.addEventListener('click', () => {
      doSave(`/resume/${resumeId}/preview`);
    });
  }

  // Auto-save every 30s
  if (resumeId) {
    setInterval(() => doSave(null), 30000);
  }

  // AI suggest summary
  const suggestBtn = document.getElementById('suggestAbout');
  if (suggestBtn) {
    suggestBtn.addEventListener('click', async () => {
      const role   = document.getElementById('role')?.value.trim()  || '';
      const skills = document.getElementById('skill_languages')?.value.trim() || '';
      const name   = document.getElementById('full_name')?.value.trim() || '';
      suggestBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i>Generating...';
      suggestBtn.disabled = true;
      try {
        const res  = await fetch('/api/suggest-summary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role, skills, name })
        });
        const data = await res.json();
        if (data.success) {
          const el = document.getElementById('about');
          if (el) { el.value = data.suggestion; el.focus(); }
        }
      } catch {}
      suggestBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles me-1"></i>AI Suggest';
      suggestBtn.disabled = false;
    });
  }

  goTo(0);
  return { goTo };
})();

// ── Save indicator ──────────────────────────────────────────────
let saveTimer;
function showSaveIndicator(text = '✓ Saved!') {
  const el = document.getElementById('saveIndicator');
  if (!el) return;
  el.textContent = text;
  el.style.display = 'flex';
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => { el.style.display = 'none'; }, 2500);
}

// ── Delete resume confirm ───────────────────────────────────────
document.querySelectorAll('.delete-resume-form').forEach(form => {
  form.addEventListener('submit', (e) => {
    if (!confirm('Delete this resume? This cannot be undone.')) e.preventDefault();
  });
});

// ── Smooth anchor links ─────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', (e) => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const offset = 80;
      window.scrollTo({ top: target.offsetTop - offset, behavior: 'smooth' });
    }
  });
});