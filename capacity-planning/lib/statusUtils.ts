/** Status-to-colour mapping and health state utilities */

import type { StatusColour } from '@/constants/statusColours';
import type { HealthStatus } from '@/types/dashboard';
import type { AvailabilityStatus } from '@/types/employee';
import type { UtilisationLevel } from '@/types/capacity';
import { UTILISATION_THRESHOLDS } from '@/constants/capacityThresholds';

/** Map health status to status colour */
export function healthToColour(health: HealthStatus): StatusColour {
  const map: Record<HealthStatus, StatusColour> = {
    green: 'green',
    amber: 'amber',
    red: 'red',
  };
  return map[health];
}

/** Map risk level to status colour */
export function riskToColour(risk: 'high' | 'medium' | 'low'): StatusColour {
  const map: Record<string, StatusColour> = {
    high: 'red',
    medium: 'amber',
    low: 'green',
  };
  return map[risk];
}

/** Map utilisation percentage to status colour */
export function utilisationToColour(percent: number): StatusColour {
  if (percent <= UTILISATION_THRESHOLDS.HEALTHY_MAX) return 'green';
  if (percent <= UTILISATION_THRESHOLDS.WATCH_MAX) return 'amber';
  return 'red';
}

/** Map utilisation percentage to level */
export function utilisationToLevel(percent: number): UtilisationLevel {
  if (percent <= UTILISATION_THRESHOLDS.HEALTHY_MAX) return 'healthy';
  if (percent <= UTILISATION_THRESHOLDS.WATCH_MAX) return 'watch';
  if (percent <= UTILISATION_THRESHOLDS.CRITICAL) return 'over-capacity';
  return 'critical';
}

/** Map availability status to colour */
export function availabilityToColour(status: AvailabilityStatus): StatusColour {
  const map: Record<AvailabilityStatus, StatusColour> = {
    'available': 'green',
    'partially-available': 'amber',
    'on-leave': 'grey',
    'public-holiday': 'blue',
    'ceremony-heavy': 'amber',
    'support-rotation': 'amber',
    'critical-risk': 'red',
  };
  return map[status];
}

/** Get privacy-preserving leave label (general view) */
export function getLeaveLabel(leaveType: string, isManagerView: boolean): string {
  if (!isManagerView) {
    return leaveType === 'none' ? 'None' : 'Unavailable';
  }

  const labels: Record<string, string> = {
    'annual': 'Annual leave',
    'sick': 'Sick leave',
    'family-responsibility': 'Family responsibility leave',
    'study': 'Study leave',
    'unpaid': 'Unpaid leave',
    'maternity': 'Maternity leave',
    'paternity': 'Paternity leave',
    'none': 'None',
  };

  return labels[leaveType] || 'Unavailable';
}
