/** Capacity and utilisation types */

export type UtilisationLevel = 'healthy' | 'watch' | 'over-capacity' | 'critical';

export interface CapacityMetric {
  label: string;
  value: string | number;
  unit?: string;
  secondaryText: string;
  trend?: 'up' | 'down' | 'flat';
  riskLevel?: 'green' | 'amber' | 'red' | 'blue' | 'grey';
}

export interface WorkloadDistribution {
  memberId: string;
  memberName: string;
  role: string;
  assignedPoints: number;
  capacityPoints: number;
  utilisationPercent: number;
}

export interface RoleCoverage {
  role: string;
  totalMembers: number;
  availableMembers: number;
  coveragePercent: number;
  isCritical: boolean;
}
