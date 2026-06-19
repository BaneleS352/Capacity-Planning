/** Employee and team member domain types */

export type AvailabilityStatus =
  | 'available'
  | 'partially-available'
  | 'on-leave'
  | 'public-holiday'
  | 'ceremony-heavy'
  | 'support-rotation'
  | 'critical-risk';

export type LeaveType =
  | 'annual'
  | 'sick'
  | 'family-responsibility'
  | 'study'
  | 'unpaid'
  | 'maternity'
  | 'paternity'
  | 'none';

export type EmployeeRole =
  | 'Backend Developer'
  | 'Frontend Developer'
  | 'Full Stack Developer'
  | 'QA Engineer'
  | 'DevOps Engineer'
  | 'Tech Lead'
  | 'Mobile Developer'
  | 'Data Engineer'
  | 'Data Scientist'
  | 'Data Science Lead'
  | 'Machine Learning Engineer'
  | 'Analytics Engineer'
  | 'UI/UX Designer';

export type RiskLevel = 'green' | 'amber' | 'red';

export interface TeamMember {
  id: string;
  name: string;
  role: EmployeeRole;
  availabilityStatus: AvailabilityStatus;
  leaveSummary: string;
  leaveType: LeaveType;
  leaveDays: number;
  dailyCapacityHours: number;
  sprintCapacityHours: number;
  assignedStoryPoints: number;
  utilisationPercent: number;
  riskLevel: RiskLevel;
  riskReason: string;
  avatarInitials: string;
}

export interface EmployeeProfile extends TeamMember {
  team: string;
  reportingLine: string;
  employmentType: string;
  location: string;
  jiraMappingStatus: 'linked' | 'unlinked';
  payspaceMappingStatus: 'linked' | 'unlinked';
  allocationPercent: number;
  upcomingLeave: UpcomingLeave[];
  currentIssues: string[];
  blockedWork: number;
  carryOverItems: number;
  historicalData: EmployeeHistoricalData;
}

export interface UpcomingLeave {
  startDate: string;
  endDate: string;
  type: LeaveType;
  days: number;
}

export interface EmployeeHistoricalData {
  sprintHistory: SprintHistoryEntry[];
  workTypeBreakdown: WorkTypeBreakdown;
}

export interface SprintHistoryEntry {
  sprintName: string;
  committed: number;
  delivered: number;
  carryOver: number;
  blockedDays: number;
  leaveDays: number;
  utilisationPercent: number;
}

export interface WorkTypeBreakdown {
  feature: number;
  bug: number;
  techDebt: number;
  support: number;
  incident: number;
}

/** Availability for a specific day in the heatmap */
export interface DayAvailability {
  date: string;
  status: AvailabilityStatus;
  label: string;
}
