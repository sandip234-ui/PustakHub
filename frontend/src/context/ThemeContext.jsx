/**
 * ThemeContext — Application-wide light/dark/system theme management.
 *
 * Supports three modes:
 *   - "light": Force light theme
 *   - "dark": Force dark theme
 *   - "system": Follow OS prefers-color-scheme
 *
 * Persists to localStorage. Applies theme class to <html> element.
 * Theme is initialized early (before React) via index.html inline script
 * to prevent FOUC (Flash of Unstyled Content).
 */

import { createContext, useCallback, useEffect, useState } from "react";

/* eslint-disable react-refresh/only-export-components */
export const ThemeContext = createContext(null);

const STORAGE_KEY = "pustakhub_theme";
const VALID_THEMES = ["light", "dark", "system"];

function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return VALID_THEMES.includes(stored) ? stored : "dark";
  } catch {
    return "dark";
  }
}

function getSystemPreference() {
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return "dark";
}

function resolveEffectiveTheme(preference) {
  if (preference === "system") return getSystemPreference();
  return preference;
}

function applyThemeToDocument(effectiveTheme) {
  const root = document.documentElement;
  if (effectiveTheme === "dark") {
    root.classList.add("dark");
    root.classList.remove("light");
  } else {
    root.classList.add("light");
    root.classList.remove("dark");
  }
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(getStoredTheme);
  const effectiveTheme = resolveEffectiveTheme(theme);

  // Apply theme whenever it changes
  useEffect(() => {
    applyThemeToDocument(effectiveTheme);
  }, [effectiveTheme]);

  // Listen for system preference changes when in "system" mode
  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e) => {
      applyThemeToDocument(e.matches ? "dark" : "light");
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  const setTheme = useCallback((newTheme) => {
    if (!VALID_THEMES.includes(newTheme)) return;
    try {
      localStorage.setItem(STORAGE_KEY, newTheme);
    } catch {
      // ignore
    }
    setThemeState(newTheme);
  }, []);

  const value = {
    theme,
    effectiveTheme,
    setTheme,
    isDark: effectiveTheme === "dark",
    isLight: effectiveTheme === "light",
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export default ThemeContext;
