/** Capacity calculation and leave impact utilities */

import { UTILISATION_THRESHOLDS } from '@/constants/capacityThresholds';
import type { UtilisationLevel } from '@/types/capacity';

/** Calculate utilisation percentage */
export function calculateUtilisation(assigned: number, capacity: number): number {
  if (capacity === 0) return 0;
  return Math.round((assigned / capacity) * 100);
}

/** Determine utilisation level from percentage */
export function getUtilisationLevel(percent: number): UtilisationLevel {
  if (percent <= UTILISATION_THRESHOLDS.HEALTHY_MAX) return 'healthy';
  if (percent <= UTILISATION_THRESHOLDS.WATCH_MAX) return 'watch';
  if (percent <= UTILISATION_THRESHOLDS.CRITICAL) return 'over-capacity';
  return 'critical';
}

/** Calculate leave impact in person-days */
export function calculateLeaveImpact(
  leaveDays: number,
  dailyCapacityHours: number,
  standardDayHours: number = 5.5
): number {
  return Math.round((leaveDays * dailyCapacityHours) / standardDayHours * 10) / 10;
}

/** Calculate adjusted capacity after leave */
export function calculateAdjustedCapacity(
  baseCapacityPersonDays: number,
  leaveImpactPersonDays: number
): number {
  return Math.max(0, baseCapacityPersonDays - leaveImpactPersonDays);
}

/** Calculate recommended sprint load based on capacity and buffer */
export function calculateRecommendedLoad(
  availablePersonDays: number,
  targetUtilisation: number = 85
): number {
  return Math.round(availablePersonDays * (targetUtilisation / 100));
}

/** Calculate how many points should be removed to reach target utilisation */
export function calculatePointsToRemove(
  committedPoints: number,
  availablePersonDays: number,
  targetUtilisation: number = 85
): number {
  const targetPoints = calculateRecommendedLoad(availablePersonDays, targetUtilisation);
  return Math.max(0, committedPoints - targetPoints);
}
