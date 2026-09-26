/**
 * CategoryIcon.jsx — Category Icon Visual Identity Component.
 *
 * Renders domain-specific Tabler SVG icons with subtle secondary color accents.
 * Provides consistent sizing, accessibility, and graceful fallback for unknown categories.
 */

import React from "react";
import { getCategoryIcon, getCategoryStyle } from "../utils/categoryIcons";

const sizeMap = {
  sm: { container: "h-8 w-8 rounded-lg", icon: 16 },
  md: { container: "h-11 w-11 rounded-xl", icon: 22 },
  lg: { container: "h-14 w-14 rounded-2xl", icon: 28 },
};

export function CategoryIcon({
  categoryName,
  size = "md",
  className = "",
  style = {},
  showBackground = true,
}) {
  const Icon = getCategoryIcon(categoryName);
  const theme = getCategoryStyle(categoryName);
  const config = sizeMap[size] || sizeMap.md;

  if (!showBackground) {
    return React.createElement(Icon, {
      size: config.icon,
      style: { color: theme.color, ...style },
      className: `shrink-0 ${className}`,
      "aria-hidden": "true",
    });
  }

  return (
    <div
      className={`flex items-center justify-center shrink-0 border transition-colors ${config.container} ${className}`}
      style={{
        backgroundColor: theme.bg,
        borderColor: theme.border,
        color: theme.color,
        ...style,
      }}
      aria-hidden="true"
    >
      {React.createElement(Icon, {
        size: config.icon,
        stroke: 1.75,
      })}
    </div>
  );
}

export default CategoryIcon;
