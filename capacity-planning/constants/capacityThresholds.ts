/** Capacity thresholds and business rules */

/** Utilisation thresholds (percentage) */
export const UTILISATION_THRESHOLDS = {
  HEALTHY_MAX: 85,
  WATCH_MAX: 100,
  OVER_CAPACITY: 100,
  CRITICAL: 120,
} as const;

/** Stale data thresholds (hours) */
export const STALE_DATA_THRESHOLDS = {
  WARNING_HOURS: 4,
  CRITICAL_HOURS: 12,
} as const;

/** Default working hours per day */
export const DEFAULT_WORKING_HOURS_PER_DAY = 5.5;

/** Default sprint length in working days */
export const DEFAULT_SPRINT_DAYS = 10;

/** Stale in-progress threshold (days in same status) */
export const STALE_IN_PROGRESS_DAYS = 3;

/** Minimum story points to flag scope creep after sprint start */
export const SCOPE_CREEP_THRESHOLD_POINTS = 10;

/** Team utilisation labels */
export const UTILISATION_LABELS: Record<string, string> = {
  healthy: 'Healthy',
  watch: 'Moderate',
  'over-capacity': 'High',
  critical: 'Critical',
};
