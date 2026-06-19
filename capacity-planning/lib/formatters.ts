/** Formatting utilities for display values */

/**
 * Format a number with a suffix unit
 * e.g. formatMetric(82, 'person-days') → '82 person-days'
 */
export function formatMetric(value: number, unit?: string): string {
  if (unit) return `${value} ${unit}`;
  return String(value);
}

/** Format percentage for display, e.g. 117 → '117%' */
export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

/** Format hours for display, e.g. 5.5 → '5.5h' */
export function formatHours(value: number): string {
  if (value === 0) return '0h';
  return `${value}h`;
}

/** Format a date string to a short display format, e.g. '15 Jun' */
export function formatShortDate(dateString: string): string {
  const date = new Date(dateString);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${date.getDate()} ${months[date.getMonth()]}`;
}

/** Format a date string to include time, e.g. '15 Jun 09:42' */
export function formatDateTime(dateString: string | null): string {
  if (!dateString) return 'Not available';
  const date = new Date(dateString);
  const short = formatShortDate(dateString);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${short} ${hours}:${minutes}`;
}

/** Format time only, e.g. '09:42' */
export function formatTime(dateString: string | null): string {
  if (!dateString) return 'Not available';
  const date = new Date(dateString);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}

/** Format relative time, e.g. '3 hours ago', 'just now' */
export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Not available';
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffMinutes < 1) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return formatDateTime(dateString);
}

/** Format story points display */
export function formatStoryPoints(value: number): string {
  return `${value} SP`;
}

/** Pluralize a word based on count */
export function pluralize(count: number, singular: string, plural?: string): string {
  if (count === 1) return `${count} ${singular}`;
  return `${count} ${plural || singular + 's'}`;
}
