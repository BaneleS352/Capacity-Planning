/** Core dashboard domain types */

export type HealthStatus = 'green' | 'amber' | 'red';

export interface Team {
  id: string;
  name: string;
  engineeringManager: string;
  scrumMaster: string;
  productOwner: string;
  department: string;
  portfolio?: string;
  isFavourite?: boolean;
}

export interface Sprint {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  dayNumber: number;
  totalDays: number;
  healthStatus: HealthStatus;
  healthReason: string;
}

export interface CapacitySummary {
  availablePersonDays: number;
  committedStoryPointEquivalent: number;
  utilisationPercent: number;
  riskLevel: RiskLevel;
  completedStoryPoints: number;
  inProgressStoryPoints: number;
  remainingStoryPoints: number;
  leaveImpactPersonDays: number;
}

export type RiskLevel = 'high' | 'medium' | 'low';

export interface DataFreshness {
  jiraLastSyncedAt: string | null;
  payspaceLastSyncedAt: string | null;
  capacityRecalculatedAt: string | null;
  staleSystems: StaleSystem[];
}

export interface StaleSystem {
  system: string;
  lastSyncedAt: string | null;
  hoursStale: number;
  message: string;
}

export interface DashboardData {
  team: Team;
  sprint: Sprint;
  capacitySummary: CapacitySummary;
  dataFreshness: DataFreshness;
}
