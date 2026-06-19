/** Mock dashboard data — realistic HollywoodBets team context */

import type { DashboardData, Team, Sprint, CapacitySummary, DataFreshness } from '@/types/dashboard';
import type { BurndownPoint, ScopeChange, PlannedVsActual } from '@/types/sprint';

export const mockTeam: Team = {
  id: 'team-payments',
  name: 'Payments Platform',
  engineeringManager: 'L. Dlamini',
  scrumMaster: 'N. van Wyk',
  productOwner: 'R. Maharaj',
  department: 'Core Platform',
  portfolio: 'Digital Channels',
  isFavourite: true,
};

export const mockSprint: Sprint = {
  id: 'sprint-24-6',
  name: 'Sprint 24.6',
  startDate: '2026-06-08',
  endDate: '2026-06-19',
  dayNumber: 6,
  totalDays: 10,
  healthStatus: 'amber',
  healthReason:
    'Capacity pressure detected. Team is planned at 104% of adjusted capacity. QA availability drops in week two due to annual leave.',
};

export const mockCapacitySummary: CapacitySummary = {
  availablePersonDays: 82,
  committedStoryPointEquivalent: 96,
  utilisationPercent: 117,
  riskLevel: 'high',
  completedStoryPoints: 38,
  inProgressStoryPoints: 24,
  remainingStoryPoints: 34,
  leaveImpactPersonDays: 14,
};

export const mockDataFreshness: DataFreshness = {
  jiraLastSyncedAt: '2026-06-15T09:42:00+02:00',
  payspaceLastSyncedAt: '2026-06-15T08:55:00+02:00',
  capacityRecalculatedAt: '2026-06-15T09:43:00+02:00',
  staleSystems: [],
};

export const mockDashboardData: DashboardData = {
  team: mockTeam,
  sprint: mockSprint,
  capacitySummary: mockCapacitySummary,
  dataFreshness: mockDataFreshness,
};

/** Available teams for team switcher */
export const mockTeams: Team[] = [
  mockTeam,
  {
    id: 'team-sportsbook',
    name: 'Sportsbook Engine',
    engineeringManager: 'T. Nkosi',
    scrumMaster: 'A. Chetty',
    productOwner: 'J. Botha',
    department: 'Betting Platform',
    portfolio: 'Digital Channels',
    isFavourite: true,
  },
  {
    id: 'team-mobile',
    name: 'Mobile Experience',
    engineeringManager: 'S. Pillay',
    scrumMaster: 'K. Moyo',
    productOwner: 'D. Govender',
    department: 'Digital Channels',
    portfolio: 'Digital Channels',
    isFavourite: false,
  },
  {
    id: 'team-promotions',
    name: 'Promotions & Bonuses',
    engineeringManager: 'M. Zulu',
    scrumMaster: 'P. Singh',
    productOwner: 'B. Ndlovu',
    department: 'Marketing Platform',
    portfolio: 'Growth',
    isFavourite: false,
  },
  {
    id: 'team-compliance',
    name: 'Compliance & Reporting',
    engineeringManager: 'F. Joubert',
    scrumMaster: 'C. Mthembu',
    productOwner: 'H. Naidoo',
    department: 'Risk & Compliance',
    portfolio: 'Governance',
    isFavourite: false,
  },
  {
    id: 'team-platform',
    name: 'Platform Infrastructure',
    engineeringManager: 'G. Pretorius',
    scrumMaster: 'W. Khumalo',
    productOwner: 'E. Reddy',
    department: 'Core Platform',
    portfolio: 'Infrastructure',
    isFavourite: false,
  },
];

/** Burndown chart data */
export const mockBurndownData: BurndownPoint[] = [
  { day: 1, date: '2026-06-08', ideal: 96, actual: 96, label: 'Mon 8' },
  { day: 2, date: '2026-06-09', ideal: 86.4, actual: 90, label: 'Tue 9' },
  { day: 3, date: '2026-06-10', ideal: 76.8, actual: 82, label: 'Wed 10' },
  { day: 4, date: '2026-06-11', ideal: 67.2, actual: 72, label: 'Thu 11' },
  { day: 5, date: '2026-06-12', ideal: 57.6, actual: 64, label: 'Fri 12' },
  { day: 6, date: '2026-06-15', ideal: 48, actual: 58, label: 'Mon 15' },
  { day: 7, date: '2026-06-16', ideal: 38.4, actual: null, label: 'Tue 16' },
  { day: 8, date: '2026-06-17', ideal: 28.8, actual: null, label: 'Wed 17' },
  { day: 9, date: '2026-06-18', ideal: 19.2, actual: null, label: 'Thu 18' },
  { day: 10, date: '2026-06-19', ideal: 0, actual: null, label: 'Fri 19' },
];

/** Scope changes after sprint start */
export const mockScopeChanges: ScopeChange[] = [
  {
    id: 'sc-1',
    date: '2026-06-10',
    type: 'added',
    issueKey: 'PAY-342',
    issueTitle: 'Emergency: Fix deposit timeout on EFT gateway',
    storyPoints: 8,
    reason: 'Production incident escalation',
    dayNumber: 3,
  },
  {
    id: 'sc-2',
    date: '2026-06-11',
    type: 'added',
    issueKey: 'PAY-345',
    issueTitle: 'Add retry logic for failed withdrawal callbacks',
    storyPoints: 5,
    reason: 'Dependency on PAY-342 fix',
    dayNumber: 4,
  },
  {
    id: 'sc-3',
    date: '2026-06-12',
    type: 're-estimated',
    issueKey: 'PAY-330',
    issueTitle: 'Refactor payment reconciliation batch job',
    storyPoints: 3,
    reason: 'Complexity increase after tech review (was 5, now 8)',
    dayNumber: 5,
  },
  {
    id: 'sc-4',
    date: '2026-06-11',
    type: 'removed',
    issueKey: 'PAY-335',
    issueTitle: 'Update payment method icons in mobile app',
    storyPoints: -3,
    reason: 'Deprioritised to accommodate incident work',
    dayNumber: 4,
  },
];

/** Planned vs actual comparison */
export const mockPlannedVsActual: PlannedVsActual[] = [
  { category: 'Story Points', planned: 96, actual: 38 },
  { category: 'Person-days', planned: 82, actual: 48 },
  { category: 'Issues', planned: 18, actual: 8 },
];
