/** Semantic colour tokens for status indicators */

export type StatusColour = 'green' | 'amber' | 'red' | 'blue' | 'grey';

/** Tailwind class mappings for status colours */
export const STATUS_BG_CLASSES: Record<StatusColour, string> = {
  green: 'bg-emerald-50',
  amber: 'bg-amber-50',
  red: 'bg-red-50',
  blue: 'bg-blue-50',
  grey: 'bg-zinc-100',
};

export const STATUS_TEXT_CLASSES: Record<StatusColour, string> = {
  green: 'text-emerald-700',
  amber: 'text-amber-700',
  red: 'text-red-700',
  blue: 'text-blue-700',
  grey: 'text-zinc-500',
};

export const STATUS_BORDER_CLASSES: Record<StatusColour, string> = {
  green: 'border-emerald-200',
  amber: 'border-amber-200',
  red: 'border-red-200',
  blue: 'border-blue-200',
  grey: 'border-zinc-200',
};

export const STATUS_DOT_CLASSES: Record<StatusColour, string> = {
  green: 'bg-emerald-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
  blue: 'bg-blue-500',
  grey: 'bg-zinc-400',
};

export const STATUS_RING_CLASSES: Record<StatusColour, string> = {
  green: 'ring-emerald-500/20',
  amber: 'ring-amber-500/20',
  red: 'ring-red-500/20',
  blue: 'ring-blue-500/20',
  grey: 'ring-zinc-400/20',
};

/** Health status labels for display */
export const HEALTH_LABELS: Record<string, string> = {
  green: 'Healthy',
  amber: 'Watch',
  red: 'At Risk',
};

/** Availability status display labels */
export const AVAILABILITY_LABELS: Record<string, string> = {
  'available': 'Available',
  'partially-available': 'Partial',
  'on-leave': 'On Leave',
  'public-holiday': 'Holiday',
  'ceremony-heavy': 'Ceremonies',
  'support-rotation': 'Support',
  'critical-risk': 'Critical',
};

/** Heatmap cell background colours */
export const HEATMAP_BG_CLASSES: Record<string, string> = {
  'available': 'bg-emerald-100 text-emerald-800',
  'partially-available': 'bg-amber-100 text-amber-800',
  'on-leave': 'bg-zinc-200 text-zinc-600',
  'public-holiday': 'bg-blue-100 text-blue-700',
  'ceremony-heavy': 'bg-purple-100 text-purple-700',
  'support-rotation': 'bg-orange-100 text-orange-700',
  'critical-risk': 'bg-red-100 text-red-700',
};
