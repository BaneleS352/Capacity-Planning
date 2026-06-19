/** Mock employee and team member data */

import type { TeamMember, EmployeeProfile, DayAvailability, AvailabilityStatus } from '@/types/employee';

export const mockTeamMembers: TeamMember[] = [
  {
    id: 'emp-1',
    name: 'A. Mokoena',
    role: 'Backend Developer',
    availabilityStatus: 'available',
    leaveSummary: 'None',
    leaveType: 'none',
    leaveDays: 0,
    dailyCapacityHours: 5.5,
    sprintCapacityHours: 55,
    assignedStoryPoints: 18,
    utilisationPercent: 82,
    riskLevel: 'green',
    riskReason: '',
    avatarInitials: 'AM',
  },
  {
    id: 'emp-2',
    name: 'S. Naidoo',
    role: 'QA Engineer',
    availabilityStatus: 'on-leave',
    leaveSummary: 'Annual leave, 3 days',
    leaveType: 'annual',
    leaveDays: 3,
    dailyCapacityHours: 0,
    sprintCapacityHours: 32,
    assignedStoryPoints: 13,
    utilisationPercent: 106,
    riskLevel: 'amber',
    riskReason: 'Reduced QA capacity. 3 days leave in sprint window.',
    avatarInitials: 'SN',
  },
  {
    id: 'emp-3',
    name: 'T. Jacobs',
    role: 'Frontend Developer',
    availabilityStatus: 'available',
    leaveSummary: 'None',
    leaveType: 'none',
    leaveDays: 0,
    dailyCapacityHours: 5,
    sprintCapacityHours: 50,
    assignedStoryPoints: 31,
    utilisationPercent: 135,
    riskLevel: 'red',
    riskReason: 'Delivery variance detected. Workload exceeds available capacity by 35%. Possible contributing factors: scope additions after sprint start, blocked dependencies.',
    avatarInitials: 'TJ',
  },
  {
    id: 'emp-4',
    name: 'D. Mthembu',
    role: 'Full Stack Developer',
    availabilityStatus: 'available',
    leaveSummary: 'None',
    leaveType: 'none',
    leaveDays: 0,
    dailyCapacityHours: 5.5,
    sprintCapacityHours: 55,
    assignedStoryPoints: 15,
    utilisationPercent: 68,
    riskLevel: 'green',
    riskReason: '',
    avatarInitials: 'DM',
  },
  {
    id: 'emp-5',
    name: 'K. Govender',
    role: 'DevOps Engineer',
    availabilityStatus: 'support-rotation',
    leaveSummary: 'None',
    leaveType: 'none',
    leaveDays: 0,
    dailyCapacityHours: 3,
    sprintCapacityHours: 30,
    assignedStoryPoints: 8,
    utilisationPercent: 73,
    riskLevel: 'amber',
    riskReason: 'Reduced capacity due to support rotation. Effective capacity is 55% of standard.',
    avatarInitials: 'KG',
  },
  {
    id: 'emp-6',
    name: 'P. van der Merwe',
    role: 'Tech Lead',
    availabilityStatus: 'ceremony-heavy',
    leaveSummary: 'None',
    leaveType: 'none',
    leaveDays: 0,
    dailyCapacityHours: 3.5,
    sprintCapacityHours: 35,
    assignedStoryPoints: 5,
    utilisationPercent: 40,
    riskLevel: 'green',
    riskReason: '',
    avatarInitials: 'PV',
  },
  {
    id: 'emp-7',
    name: 'L. Sithole',
    role: 'Backend Developer',
    availabilityStatus: 'on-leave',
    leaveSummary: 'Family responsibility leave, 2 days',
    leaveType: 'family-responsibility',
    leaveDays: 2,
    dailyCapacityHours: 0,
    sprintCapacityHours: 38.5,
    assignedStoryPoints: 12,
    utilisationPercent: 86,
    riskLevel: 'amber',
    riskReason: 'Reduced sprint capacity due to leave. Current workload close to adjusted capacity.',
    avatarInitials: 'LS',
  },
  {
    id: 'emp-8',
    name: 'R. Patel',
    role: 'Mobile Developer',
    availabilityStatus: 'available',
    leaveSummary: 'None',
    leaveType: 'none',
    leaveDays: 0,
    dailyCapacityHours: 5.5,
    sprintCapacityHours: 55,
    assignedStoryPoints: 10,
    utilisationPercent: 50,
    riskLevel: 'green',
    riskReason: '',
    avatarInitials: 'RP',
  },
];

/** Mock employee profile for drawer */
export const mockEmployeeProfile: EmployeeProfile = {
  ...mockTeamMembers[2], // T. Jacobs — the overloaded frontend dev
  team: 'Payments Platform',
  reportingLine: 'L. Dlamini → S. Pillay (CTO)',
  employmentType: 'Permanent',
  location: 'Durban, KZN',
  jiraMappingStatus: 'linked',
  payspaceMappingStatus: 'linked',
  allocationPercent: 100,
  upcomingLeave: [
    { startDate: '2026-07-01', endDate: '2026-07-04', type: 'annual', days: 4 },
  ],
  currentIssues: ['PAY-330', 'PAY-331', 'PAY-342', 'PAY-345', 'PAY-347'],
  blockedWork: 1,
  carryOverItems: 2,
  historicalData: {
    sprintHistory: [
      { sprintName: 'Sprint 24.3', committed: 21, delivered: 18, carryOver: 3, blockedDays: 1, leaveDays: 0, utilisationPercent: 95 },
      { sprintName: 'Sprint 24.4', committed: 18, delivered: 18, carryOver: 0, blockedDays: 0, leaveDays: 0, utilisationPercent: 88 },
      { sprintName: 'Sprint 24.5', committed: 24, delivered: 21, carryOver: 3, blockedDays: 2, leaveDays: 0, utilisationPercent: 110 },
      { sprintName: 'Sprint 24.6', committed: 31, delivered: 12, carryOver: 0, blockedDays: 1, leaveDays: 0, utilisationPercent: 135 },
    ],
    workTypeBreakdown: {
      feature: 55,
      bug: 20,
      techDebt: 10,
      support: 10,
      incident: 5,
    },
  },
};

/** Generate heatmap data for each team member across sprint days */
export function generateMockHeatmapData(
  memberIds: string[],
  sprintDays: string[]
): Record<string, DayAvailability[]> {
  const heatmap: Record<string, DayAvailability[]> = {};

  const leaveSchedule: Record<string, Record<string, AvailabilityStatus>> = {
    'emp-2': {
      '2026-06-16': 'on-leave',
      '2026-06-17': 'on-leave',
      '2026-06-18': 'on-leave',
    },
    'emp-7': {
      '2026-06-11': 'on-leave',
      '2026-06-12': 'on-leave',
    },
    'emp-5': {
      '2026-06-08': 'support-rotation',
      '2026-06-09': 'support-rotation',
      '2026-06-10': 'support-rotation',
      '2026-06-11': 'support-rotation',
      '2026-06-12': 'support-rotation',
    },
    'emp-6': {
      '2026-06-09': 'ceremony-heavy',
      '2026-06-16': 'ceremony-heavy',
    },
  };

  for (const memberId of memberIds) {
    heatmap[memberId] = sprintDays.map(date => {
      const override = leaveSchedule[memberId]?.[date];
      return {
        date,
        status: override || 'available',
        label: override
          ? override === 'on-leave' ? 'Leave' :
            override === 'support-rotation' ? 'Support' :
            override === 'ceremony-heavy' ? 'Ceremonies' : 'Available'
          : 'Available',
      };
    });
  }

  return heatmap;
}
