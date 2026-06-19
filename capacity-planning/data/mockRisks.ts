/** Mock risk signal data */

import type { RiskSignal } from '@/types/risk';

export const mockRiskSignals: RiskSignal[] = [
  {
    id: 'risk-1',
    severity: 'high',
    type: 'over-utilisation',
    title: 'Team utilisation is 117%',
    whyItMatters:
      'The team has 96 story-point equivalent committed against 82 effective person-days. Sustained over-utilisation leads to quality risks, missed deadlines, and team burnout.',
    contributingFactors: [
      '2 engineers on leave (S. Naidoo — 3 days, L. Sithole — 2 days)',
      'QA capacity reduced by 40% in week two',
      '16 story points added after sprint start (PAY-342, PAY-345, PAY-348)',
      '2 issues blocked (PAY-330, PAY-347)',
    ],
    recommendation:
      'Remove approximately 12 story points of non-critical work or move to the next sprint. Consider deferring PAY-331 (5 SP) and PAY-340 (5 SP).',
  },
  {
    id: 'risk-2',
    severity: 'high',
    type: 'blocked-work',
    title: '2 issues blocked for 3+ days',
    whyItMatters:
      'Blocked issues (PAY-330 and PAY-347) represent 13 story points of stalled work. If not unblocked soon, these will become carry-over and further increase next sprint pressure.',
    contributingFactors: [
      'PAY-330: Blocked on DBA team database migration approval',
      'PAY-347: Blocked on security team review of biometric SDK',
      'Both blockers are external dependencies outside team control',
    ],
    recommendation:
      'Escalate both blockers to engineering management today. Set a 24-hour resolution deadline. If unresolved, move to next sprint and adjust capacity plan.',
  },
  {
    id: 'risk-3',
    severity: 'medium',
    type: 'scope-creep',
    title: '16 story points added after sprint start',
    whyItMatters:
      'Scope additions (PAY-342, PAY-345, PAY-348) have increased committed work by 17% without corresponding capacity increase. This erodes the sprint plan and makes forecasting unreliable.',
    contributingFactors: [
      'PAY-342 (8 SP): Production incident escalation — unavoidable',
      'PAY-345 (5 SP): Follow-on dependency from PAY-342',
      'PAY-348 (3 SP): Documentation task added mid-sprint',
      'Only PAY-335 (-3 SP) was removed to compensate',
    ],
    recommendation:
      'Net scope increase is +13 SP. Defer PAY-348 documentation task (3 SP) to next sprint. For future sprints, reserve a 15% buffer for unplanned work.',
  },
  {
    id: 'risk-4',
    severity: 'medium',
    type: 'role-coverage',
    title: 'QA coverage drops to 60% in week two',
    whyItMatters:
      'S. Naidoo (sole QA engineer) is on leave for 3 days in week two. Without QA capacity, completed work cannot be validated, creating a bottleneck that delays delivery.',
    contributingFactors: [
      'Single QA engineer on the team',
      'No cross-trained backup for QA activities',
      '5 issues require QA validation before sprint end',
    ],
    recommendation:
      'Identify a developer who can assist with QA validation for critical issues. Prioritise PAY-332 regression suite before S. Naidoo goes on leave.',
  },
  {
    id: 'risk-5',
    severity: 'low',
    type: 'carry-over',
    title: '2 carry-over items from previous sprint',
    whyItMatters:
      'PAY-327 and PAY-328 were carried over from Sprint 24.5. Recurring carry-over indicates systemic estimation or capacity issues.',
    contributingFactors: [
      'PAY-327 (3 SP): Bug fix delayed by unclear requirements',
      'PAY-328 (8 SP): Design review took longer than estimated',
      'Both assigned to T. Jacobs who is currently at 135% utilisation',
    ],
    recommendation:
      'Monitor T. Jacobs workload. Consider redistributing PAY-331 (5 SP) to R. Patel who has capacity at 50% utilisation.',
  },
  {
    id: 'risk-6',
    severity: 'medium',
    type: 'unassigned-work',
    title: '1 high-priority issue unassigned',
    whyItMatters:
      'PAY-348 is high-priority but has no assignee. Unassigned high-priority work late in a sprint risks being overlooked or becoming carry-over.',
    contributingFactors: [
      'Added after sprint start without assignment',
      'Team is already at 117% utilisation',
      'No clear owner for documentation tasks',
    ],
    recommendation:
      'Assign PAY-348 to R. Patel (50% utilisation) or defer to next sprint if documentation is not sprint-critical.',
  },
];
