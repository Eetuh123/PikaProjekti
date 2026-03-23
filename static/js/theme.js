/**
 * theme.js — Light/dark mode toggle.
 *
 * Persists the user's preference in localStorage.
 * Applies the [data-theme="dark"] attribute to <html>.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "booking-theme";
  const DARK = "dark";
  const LIGHT = "light";

  /** Read saved preference or fall back to OS preference. */
  function getPreference() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === DARK || saved === LIGHT) return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? DARK : LIGHT;
  }

  /** Apply theme to <html> element. */
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  /** Update the toggle button's aria-label and icon. */
  function updateToggleButton(theme) {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    const isDark = theme === DARK;
    btn.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
    btn.setAttribute("aria-pressed", String(isDark));
    const icon = btn.querySelector("[data-theme-icon]");
    if (icon) {
      icon.textContent = isDark ? "☀️" : "🌙";
    }
  }

  /** Toggle between light and dark. */
  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || LIGHT;
    const next = current === DARK ? LIGHT : DARK;
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
    updateToggleButton(next);
  }

  // Apply theme immediately (before paint) to avoid flash.
  const initialTheme = getPreference();
  applyTheme(initialTheme);

  // Wire up the button once the DOM is ready.
  document.addEventListener("DOMContentLoaded", function () {
    updateToggleButton(initialTheme);
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", toggleTheme);
    }
  });
})();
