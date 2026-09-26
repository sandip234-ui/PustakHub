/**
 * categoryIcons.js — Centralized Category Icon & Accent Color Mapping.
 *
 * Uses Tabler Icons (@tabler/icons-react) for domain/category visual identity,
 * paired with subtle secondary color tokens that work seamlessly across
 * both Light and Dark themes.
 *
 * UI actions and standard controls remain exclusively on Lucide icons.
 */

import {
  IconAtom,
  IconBinaryTree,
  IconBook,
  IconBracketsContain,
  IconBrain,
  IconBriefcase,
  IconChartDots,
  IconChartInfographic,
  IconCloudNetwork,
  IconCpu,
  IconDatabase,
  IconDeviceDesktopAnalytics,
  IconDna,
  IconHistory,
  IconInfinity,
  IconMathFunction,
  IconScale,
  IconShieldLock,
  IconSparkles,
  IconTerminal2,
  IconWorldWww,
} from "@tabler/icons-react";

/**
 * Tabler Icon component mapping for the 20 canonical categories.
 */
export const CATEGORY_ICONS = {
  "Algorithms & Data Structures": IconBinaryTree,
  "Artificial Intelligence": IconBrain,
  "Bioinformatics & Genomics": IconDna,
  "Business Strategy & Technology": IconBriefcase,
  "Cognitive Science & HCI": IconDeviceDesktopAnalytics,
  "Computer Networks & Cloud": IconCloudNetwork,
  "Computer Science & Theory": IconTerminal2,
  "Cybersecurity & Cryptography": IconShieldLock,
  "Data Science & Big Data": IconChartDots,
  "Database Systems & Storage": IconDatabase,
  "DevOps & Reliability Engineering": IconInfinity,
  "Economics & Financial Technology": IconChartInfographic,
  "History of Computing": IconHistory,
  "Machine Learning & Deep Learning": IconSparkles,
  "Mathematics & Discrete Structures": IconMathFunction,
  "Operating Systems & Kernel": IconCpu,
  "Philosophy of Technology & Ethics": IconScale,
  "Quantum Computing & Physics": IconAtom,
  "Software Engineering & Architecture": IconBracketsContain,
  "Web Development & Frontend": IconWorldWww,
};

/**
 * Subtle secondary accent styles for categories (icon color, icon background, badge styles).
 * Restrained to maintain dominance of PustakHub's primary indigo visual identity.
 */
export const CATEGORY_STYLES = {
  "Algorithms & Data Structures": {
    color: "#10b981", // Emerald
    bg: "rgba(16, 185, 129, 0.12)",
    border: "rgba(16, 185, 129, 0.25)",
    badgeBg: "rgba(16, 185, 129, 0.10)",
    badgeBorder: "rgba(16, 185, 129, 0.22)",
    badgeText: "#10b981",
  },
  "Artificial Intelligence": {
    color: "#a855f7", // Violet / Purple
    bg: "rgba(168, 85, 247, 0.12)",
    border: "rgba(168, 85, 247, 0.25)",
    badgeBg: "rgba(168, 85, 247, 0.10)",
    badgeBorder: "rgba(168, 85, 247, 0.22)",
    badgeText: "#a855f7",
  },
  "Bioinformatics & Genomics": {
    color: "#f43f5e", // Rose
    bg: "rgba(244, 63, 94, 0.12)",
    border: "rgba(244, 63, 94, 0.25)",
    badgeBg: "rgba(244, 63, 94, 0.10)",
    badgeBorder: "rgba(244, 63, 94, 0.22)",
    badgeText: "#f43f5e",
  },
  "Business Strategy & Technology": {
    color: "#f59e0b", // Amber
    bg: "rgba(245, 158, 11, 0.12)",
    border: "rgba(245, 158, 11, 0.25)",
    badgeBg: "rgba(245, 158, 11, 0.10)",
    badgeBorder: "rgba(245, 158, 11, 0.22)",
    badgeText: "#f59e0b",
  },
  "Cognitive Science & HCI": {
    color: "#0ea5e9", // Sky
    bg: "rgba(14, 165, 233, 0.12)",
    border: "rgba(14, 165, 233, 0.25)",
    badgeBg: "rgba(14, 165, 233, 0.10)",
    badgeBorder: "rgba(14, 165, 233, 0.22)",
    badgeText: "#0ea5e9",
  },
  "Computer Networks & Cloud": {
    color: "#3b82f6", // Blue
    bg: "rgba(59, 130, 246, 0.12)",
    border: "rgba(59, 130, 246, 0.25)",
    badgeBg: "rgba(59, 130, 246, 0.10)",
    badgeBorder: "rgba(59, 130, 246, 0.22)",
    badgeText: "#3b82f6",
  },
  "Computer Science & Theory": {
    color: "#6366f1", // Indigo
    bg: "rgba(99, 102, 241, 0.12)",
    border: "rgba(99, 102, 241, 0.25)",
    badgeBg: "rgba(99, 102, 241, 0.10)",
    badgeBorder: "rgba(99, 102, 241, 0.22)",
    badgeText: "#6366f1",
  },
  "Cybersecurity & Cryptography": {
    color: "#ef4444", // Red
    bg: "rgba(239, 68, 68, 0.12)",
    border: "rgba(239, 68, 68, 0.25)",
    badgeBg: "rgba(239, 68, 68, 0.10)",
    badgeBorder: "rgba(239, 68, 68, 0.22)",
    badgeText: "#ef4444",
  },
  "Data Science & Big Data": {
    color: "#8b5cf6", // Purple
    bg: "rgba(139, 92, 246, 0.12)",
    border: "rgba(139, 92, 246, 0.25)",
    badgeBg: "rgba(139, 92, 246, 0.10)",
    badgeBorder: "rgba(139, 92, 246, 0.22)",
    badgeText: "#8b5cf6",
  },
  "Database Systems & Storage": {
    color: "#10b981", // Emerald
    bg: "rgba(16, 185, 129, 0.12)",
    border: "rgba(16, 185, 129, 0.25)",
    badgeBg: "rgba(16, 185, 129, 0.10)",
    badgeBorder: "rgba(16, 185, 129, 0.22)",
    badgeText: "#10b981",
  },
  "DevOps & Reliability Engineering": {
    color: "#f97316", // Orange
    bg: "rgba(249, 115, 22, 0.12)",
    border: "rgba(249, 115, 22, 0.25)",
    badgeBg: "rgba(249, 115, 22, 0.10)",
    badgeBorder: "rgba(249, 115, 22, 0.22)",
    badgeText: "#f97316",
  },
  "Economics & Financial Technology": {
    color: "#059669", // Dark Emerald / Gold accent
    bg: "rgba(5, 150, 105, 0.12)",
    border: "rgba(5, 150, 105, 0.25)",
    badgeBg: "rgba(5, 150, 105, 0.10)",
    badgeBorder: "rgba(5, 150, 105, 0.22)",
    badgeText: "#059669",
  },
  "History of Computing": {
    color: "#a1a1aa", // Warm Zinc / Slate
    bg: "rgba(161, 161, 170, 0.12)",
    border: "rgba(161, 161, 170, 0.25)",
    badgeBg: "rgba(161, 161, 170, 0.10)",
    badgeBorder: "rgba(161, 161, 170, 0.22)",
    badgeText: "var(--text-secondary)",
  },
  "Machine Learning & Deep Learning": {
    color: "#d946ef", // Fuchsia
    bg: "rgba(217, 70, 239, 0.12)",
    border: "rgba(217, 70, 239, 0.25)",
    badgeBg: "rgba(217, 70, 239, 0.10)",
    badgeBorder: "rgba(217, 70, 239, 0.22)",
    badgeText: "#d946ef",
  },
  "Mathematics & Discrete Structures": {
    color: "#eab308", // Yellow / Gold
    bg: "rgba(234, 179, 8, 0.12)",
    border: "rgba(234, 179, 8, 0.25)",
    badgeBg: "rgba(234, 179, 8, 0.10)",
    badgeBorder: "rgba(234, 179, 8, 0.22)",
    badgeText: "#ca8a04",
  },
  "Operating Systems & Kernel": {
    color: "#64748b", // Slate
    bg: "rgba(100, 116, 139, 0.12)",
    border: "rgba(100, 116, 139, 0.25)",
    badgeBg: "rgba(100, 116, 139, 0.10)",
    badgeBorder: "rgba(100, 116, 139, 0.22)",
    badgeText: "#64748b",
  },
  "Philosophy of Technology & Ethics": {
    color: "#06b6d4", // Cyan
    bg: "rgba(6, 182, 212, 0.12)",
    border: "rgba(6, 182, 212, 0.25)",
    badgeBg: "rgba(6, 182, 212, 0.10)",
    badgeBorder: "rgba(6, 182, 212, 0.22)",
    badgeText: "#06b6d4",
  },
  "Quantum Computing & Physics": {
    color: "#818cf8", // Indigo Accent
    bg: "rgba(129, 140, 248, 0.12)",
    border: "rgba(129, 140, 248, 0.25)",
    badgeBg: "rgba(129, 140, 248, 0.10)",
    badgeBorder: "rgba(129, 140, 248, 0.22)",
    badgeText: "#818cf8",
  },
  "Software Engineering & Architecture": {
    color: "#f97316", // Amber / Orange
    bg: "rgba(249, 115, 22, 0.12)",
    border: "rgba(249, 115, 22, 0.25)",
    badgeBg: "rgba(249, 115, 22, 0.10)",
    badgeBorder: "rgba(249, 115, 22, 0.22)",
    badgeText: "#f97316",
  },
  "Web Development & Frontend": {
    color: "#14b8a6", // Teal
    bg: "rgba(20, 184, 166, 0.12)",
    border: "rgba(20, 184, 166, 0.25)",
    badgeBg: "rgba(20, 184, 166, 0.10)",
    badgeBorder: "rgba(20, 184, 166, 0.22)",
    badgeText: "#14b8a6",
  },
};

/**
 * Default fallback style when a category is unknown or missing.
 */
const DEFAULT_CATEGORY_STYLE = {
  color: "var(--primary)",
  bg: "var(--primary-soft)",
  border: "rgba(99, 102, 241, 0.25)",
  badgeBg: "var(--primary-soft)",
  badgeBorder: "rgba(99, 102, 241, 0.2)",
  badgeText: "var(--primary)",
};

/**
 * Retrieves the Tabler icon for a category name with safe fallback to IconBook.
 * @param {string} categoryName
 * @returns {import("react").ComponentType}
 */
export function getCategoryIcon(categoryName) {
  if (!categoryName || typeof categoryName !== "string") {
    return IconBook;
  }
  const trimmed = categoryName.trim();
  return CATEGORY_ICONS[trimmed] || IconBook;
}

/**
 * Retrieves the secondary styling tokens for a category name with safe fallback.
 * @param {string} categoryName
 * @returns {typeof DEFAULT_CATEGORY_STYLE}
 */
export function getCategoryStyle(categoryName) {
  if (!categoryName || typeof categoryName !== "string") {
    return DEFAULT_CATEGORY_STYLE;
  }
  const trimmed = categoryName.trim();
  return CATEGORY_STYLES[trimmed] || DEFAULT_CATEGORY_STYLE;
}
