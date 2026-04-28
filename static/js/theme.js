/* ═══════════════════════════════════════════════════════════════════
   ServerWatch — Shared Theme Engine
   Include on every page: <script src="/static/js/theme.js"></script>
   Place BEFORE closing </body> tag.
═══════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Core apply ──────────────────────────────────────────────────────────────
  function resolveTheme(pref) {
    if (pref === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return pref; // 'dark' or 'light'
  }

  function applyTheme(pref) {
    const resolved = resolveTheme(pref || 'auto');
    document.documentElement.setAttribute('data-theme', resolved);

    // Update all toggle buttons on the page
    ['dark', 'light', 'auto'].forEach(function (t) {
      var btn = document.getElementById('btn-theme-' + t);
      if (btn) btn.classList.toggle('active', t === pref);
    });
  }

  // ── Public setter ───────────────────────────────────────────────────────────
  window.setTheme = function (pref) {
    localStorage.setItem('sw-theme', pref);
    applyTheme(pref);
  };

  // ── Init on load ────────────────────────────────────────────────────────────
  function init() {
    var saved = localStorage.getItem('sw-theme') || 'auto';
    applyTheme(saved);

    // Re-apply when OS dark/light preference changes (for auto mode)
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
      var current = localStorage.getItem('sw-theme') || 'auto';
      if (current === 'auto') applyTheme('auto');
    });
  }

  // Run immediately so there's no flash of wrong theme
  init();
  document.addEventListener('DOMContentLoaded', init);
})();

/* ── Toast helper — available globally on every page ── */
(function () {
  var _timer;
  window.showToast = function (msg, type) {
    type = type || 'success';
    var el = document.getElementById('toast');
    if (!el) return;
    el.className = '';
    el.innerHTML =
      '<i class="fas fa-' + (type === 'success' ? 'circle-check' : 'circle-exclamation') + '"></i> ' + msg;
    el.classList.add('show', type);
    clearTimeout(_timer);
    _timer = setTimeout(function () { el.classList.remove('show'); }, 3200);
  };
})();