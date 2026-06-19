import type { DashboardData, DataFreshness, HealthStatus, RiskLevel, Sprint, Team } from '@/types/dashboard';
import type { AvailabilityStatus, EmployeeRole, TeamMember } from '@/types/employee';
import type { IssuePriority, IssueStatus, IssueType, JiraIssue } from '@/types/jira';
import type { RiskSeverity, RiskSignal, RiskType } from '@/types/risk';
import type { BurndownPoint, ScopeChange } from '@/types/sprint';
import type {
  ApiJiraIssue,
  ApiRisk,
  ApiSprint,
  ApiSprintTimeline,
  ApiTeam,
  ApiTeamDashboard,
} from './types';

export interface DashboardView {
  data: DashboardData;
  members: TeamMember[];
  issues: JiraIssue[];
  risks: RiskSignal[];
  burndown: BurndownPoint[];
  scopeChanges: ScopeChange[];
}

const EMPLOYEE_ROLES: EmployeeRole[] = [
  'Backend Developer',
  'Frontend Developer',
  'Full Stack Developer',
  'QA Engineer',
  'DevOps Engineer',
  'Tech Lead',
  'Mobile Developer',
  'Data Engineer',
  'Data Scientist',
  'Data Science Lead',
  'Machine Learning Engineer',
  'Analytics Engineer',
  'UI/UX Designer',
];

const ISSUE_STATUSES: IssueStatus[] = ['To Do', 'In Progress', 'In Review', 'QA', 'Done', 'Blocked'];
const ISSUE_PRIORITIES: IssuePriority[] = ['Critical', 'High', 'Medium', 'Low'];
const ISSUE_TYPES: IssueType[] = ['Story', 'Bug', 'Task', 'Tech Debt', 'Spike', 'Sub-task'];

export function mapApiTeam(team: ApiTeam): Team {
  return {
    id: team.id,
    name: team.name,
    engineeringManager: setting(team.settings, 'engineering_manager') || 'Not assigned',
    scrumMaster: setting(team.settings, 'scrum_master') || 'Not assigned',
    productOwner: setting(team.settings, 'product_owner') || 'Not assigned',
    department: team.department || 'Unassigned',
    portfolio: setting(team.settings, 'portfolio') || undefined,
    isFavourite: Boolean(team.settings.is_favourite),
  };
}

export function mapApiSprint(sprint: ApiSprint, riskLevel = 'healthy', reason = ''): Sprint {
  const workingDates = getWorkingDates(sprint.start_at, sprint.end_at);
  const today = dateKey(new Date());
  const completedDays = workingDates.filter(date => date <= today).length;

  return {
    id: sprint.id,
    name: sprint.name,
    startDate: sprint.start_at,
    endDate: sprint.end_at,
    dayNumber: Math.min(Math.max(completedDays, 1), Math.max(workingDates.length, 1)),
    totalDays: Math.max(workingDates.length, 1),
    healthStatus: mapHealthStatus(riskLevel),
    healthReason: reason || sprint.goal || 'No active delivery risks were reported by the API.',
  };
}

export function adaptDashboard(
  dashboard: ApiTeamDashboard,
  timeline: ApiSprintTimeline,
): DashboardView {
  const team = mapApiTeam(dashboard.team);
  const primaryRisk = [...dashboard.risks]
    .sort((a, b) => severityRank(b.severity) - severityRank(a.severity))[0];
  const sprint = mapApiSprint(
    dashboard.sprint,
    dashboard.capacity?.risk_level,
    primaryRisk?.message,
  );
  const issues = dashboard.issues.map(issue => mapIssue(issue, dashboard.sprint));
  const capacity = dashboard.capacity;
  const workingHours = number(dashboard.team.working_hours_per_day, 8);
  const freshness = mapFreshness(dashboard);

  const data: DashboardData = {
    team,
    sprint,
    capacitySummary: {
      availablePersonDays: number(capacity?.effective_person_days),
      committedStoryPointEquivalent: capacity
        ? number(capacity.committed_story_points) + number(capacity.added_story_points) - number(capacity.removed_story_points)
        : 0,
      utilisationPercent: number(capacity?.utilization_percent),
      riskLevel: mapRiskLevel(capacity?.risk_level),
      completedStoryPoints: number(capacity?.completed_story_points),
      inProgressStoryPoints: number(capacity?.in_progress_story_points),
      remainingStoryPoints: number(capacity?.remaining_story_points),
      leaveImpactPersonDays: workingHours > 0
        ? round(number(capacity?.leave_impact_hours) / workingHours, 1)
        : 0,
    },
    dataFreshness: freshness,
  };

  return {
    data,
    members: dashboard.members.map(member => {
      const snapshot = member.capacity;
      const assigned = number(snapshot?.assigned_story_points);
      const effectiveDays = number(snapshot?.effective_person_days);
      const capacityPoints = capacity?.story_points_per_effective_day
        ? effectiveDays * number(capacity.story_points_per_effective_day)
        : effectiveDays;
      const utilisation = capacityPoints > 0 ? Math.round((assigned / capacityPoints) * 100) : 0;
      const grossHours = number(snapshot?.gross_hours);
      const leaveHours = number(snapshot?.leave_hours);
      const workingDays = number(snapshot?.working_days);
      const leaveDays = workingHours > 0 ? round(leaveHours / workingHours, 1) : 0;
      const availability = mapAvailability(leaveHours, grossHours);
      const risk = utilisation > 100 ? 'red' : utilisation > 85 ? 'amber' : 'green';

      return {
        id: member.employee.id,
        name: member.employee.full_name,
        role: mapEmployeeRole(member.employee.role_name),
        availabilityStatus: availability,
        leaveSummary: leaveDays ? `${leaveDays} person-days unavailable` : 'None',
        leaveType: leaveDays ? 'annual' : 'none',
        leaveDays,
        dailyCapacityHours: workingDays > 0 ? round(number(snapshot?.net_hours) / workingDays, 1) : 0,
        sprintCapacityHours: round(number(snapshot?.net_hours), 1),
        assignedStoryPoints: assigned,
        utilisationPercent: utilisation,
        riskLevel: risk,
        riskReason: risk === 'red' ? 'Assigned work exceeds calculated individual capacity.' : '',
        avatarInitials: initials(member.employee.full_name),
      };
    }),
    issues,
    risks: dashboard.risks.map(mapRisk),
    burndown: mapBurndown(timeline, capacity?.committed_story_points),
    scopeChanges: timeline.issues.flatMap(issue => mapScopeChanges(issue, dashboard.sprint)),
  };
}

function mapFreshness(dashboard: ApiTeamDashboard): DataFreshness {
  const staleSystems = dashboard.freshness.stale_sources.map(source => ({
    system: source,
    lastSyncedAt: source === 'jira'
      ? dashboard.freshness.jira_last_synced_at
      : dashboard.freshness.payspace_last_synced_at,
    hoursStale: 0,
    message: `${titleCase(source)} data is stale or has not completed an initial sync.`,
  }));

  return {
    jiraLastSyncedAt: dashboard.freshness.jira_last_synced_at,
    payspaceLastSyncedAt: dashboard.freshness.payspace_last_synced_at,
    capacityRecalculatedAt: dashboard.freshness.capacity_calculated_at,
    staleSystems,
  };
}

function mapIssue(issue: ApiJiraIssue, sprint: ApiSprint): JiraIssue {
  const fields = issue.normalized_fields;
  const status = normalizeChoice(issue.blocked ? 'Blocked' : issue.status, ISSUE_STATUSES, 'To Do');
  const priority = normalizeChoice(titleCase(issue.priority || 'Medium'), ISSUE_PRIORITIES, 'Medium');
  const issueType = normalizeChoice(titleCase(issue.issue_type || 'Task'), ISSUE_TYPES, 'Task');
  const assigneeName = typeof fields.assignee_name === 'string' ? fields.assignee_name : null;
  const labels = Array.isArray(fields.labels)
    ? fields.labels.filter((label): label is string => typeof label === 'string')
    : [];
  const daysInStatus = typeof fields.days_in_status === 'number'
    ? fields.days_in_status
    : Math.max(0, daysBetween(issue.source_updated_at, new Date().toISOString()));

  return {
    id: issue.id,
    key: issue.issue_key,
    title: issue.summary,
    assignee: assigneeName,
    assigneeId: issue.assignee_employee_id,
    status,
    priority,
    epic: issue.epic_key || 'No epic',
    issueType,
    storyPoints: number(issue.story_points),
    blocked: issue.blocked,
    blockedReason: typeof fields.blocked_reason === 'string' ? fields.blocked_reason : undefined,
    carryOver: Boolean(fields.carry_over),
    addedAfterSprintStart: Boolean(
      issue.added_to_sprint_at && new Date(issue.added_to_sprint_at) > new Date(sprint.start_at),
    ),
    dueDate: typeof fields.due_date === 'string' ? fields.due_date : null,
    daysInStatus,
    labels,
  };
}

function mapRisk(risk: ApiRisk): RiskSignal {
  const factors = Array.isArray(risk.context.contributing_factors)
    ? risk.context.contributing_factors.filter((item): item is string => typeof item === 'string')
    : [];

  return {
    id: risk.id,
    severity: mapRiskSeverity(risk.severity),
    type: mapRiskType(risk.risk_type),
    title: titleCase(risk.risk_type.replaceAll('_', ' ')),
    whyItMatters: risk.message,
    contributingFactors: factors,
    recommendation: risk.recommendation || 'Review the contributing capacity and delivery signals.',
  };
}

function mapBurndown(timeline: ApiSprintTimeline, committedValue?: string): BurndownPoint[] {
  const dates = getWorkingDates(timeline.sprint.start_at, timeline.sprint.end_at);
  const snapshots = [...timeline.snapshots].sort(
    (a, b) => new Date(a.captured_at).getTime() - new Date(b.captured_at).getTime(),
  );
  const initial = snapshots[0]
    ? number(snapshots[0].committed_story_points)
    : number(committedValue);
  const today = dateKey(new Date());

  return dates.map((date, index) => {
    const matching = snapshots.filter(snapshot => dateKey(new Date(snapshot.captured_at)) <= date).at(-1);
    const actual = date <= today
      ? matching
        ? Math.max(
          0,
          number(matching.committed_story_points) + number(matching.added_story_points)
            - number(matching.removed_story_points) - number(matching.completed_story_points),
        )
        : index === 0 ? initial : null
      : null;

    return {
      day: index + 1,
      date,
      ideal: round(initial * (1 - index / Math.max(dates.length - 1, 1)), 1),
      actual,
      label: new Intl.DateTimeFormat('en-ZA', { weekday: 'short', day: 'numeric' })
        .format(new Date(`${date}T12:00:00Z`)),
    };
  });
}

function mapScopeChanges(issue: ApiJiraIssue, sprint: ApiSprint): ScopeChange[] {
  const changes: ScopeChange[] = [];
  const sprintStart = new Date(sprint.start_at);

  if (issue.added_to_sprint_at && new Date(issue.added_to_sprint_at) > sprintStart) {
    changes.push(scopeChange(issue, sprint, 'added', issue.added_to_sprint_at, number(issue.story_points)));
  }
  if (issue.removed_from_sprint_at) {
    changes.push(scopeChange(issue, sprint, 'removed', issue.removed_from_sprint_at, -number(issue.story_points)));
  }
  return changes;
}

function scopeChange(
  issue: ApiJiraIssue,
  sprint: ApiSprint,
  type: ScopeChange['type'],
  date: string,
  points: number,
): ScopeChange {
  return {
    id: `${issue.id}-${type}`,
    date,
    type,
    issueKey: issue.issue_key,
    issueTitle: issue.summary,
    storyPoints: points,
    reason: typeof issue.normalized_fields.scope_change_reason === 'string'
      ? issue.normalized_fields.scope_change_reason
      : 'Reported by Jira synchronization',
    dayNumber: Math.max(1, daysBetween(dateKey(new Date(sprint.start_at)), dateKey(new Date(date))) + 1),
  };
}

function mapHealthStatus(value?: string): HealthStatus {
  if (value === 'critical' || value === 'high') return 'red';
  if (value === 'medium' || value === 'warning') return 'amber';
  return 'green';
}

function mapRiskLevel(value?: string): RiskLevel {
  if (value === 'critical' || value === 'high') return 'high';
  if (value === 'medium' || value === 'warning') return 'medium';
  return 'low';
}

function mapRiskSeverity(value: string): RiskSeverity {
  if (value === 'critical' || value === 'high') return 'high';
  if (value === 'medium' || value === 'warning') return 'medium';
  return 'low';
}

function mapRiskType(value: string): RiskType {
  const normalized = value.toLowerCase();
  if (normalized.includes('utilization')) return 'over-utilisation';
  if (normalized.includes('leave') || normalized.includes('role')) return 'leave-impact';
  if (normalized.includes('scope')) return 'scope-creep';
  if (normalized.includes('blocked')) return 'blocked-work';
  if (normalized.includes('carry')) return 'carry-over';
  if (normalized.includes('stale') || normalized.includes('data')) return 'stale-data';
  if (normalized.includes('unassigned')) return 'unassigned-work';
  return 'role-coverage';
}

function mapEmployeeRole(value: string): EmployeeRole {
  return EMPLOYEE_ROLES.find(role => role.toLowerCase() === value.toLowerCase())
    || 'Full Stack Developer';
}

function mapAvailability(leaveHours: number, grossHours: number): AvailabilityStatus {
  if (grossHours > 0 && leaveHours >= grossHours) return 'on-leave';
  if (leaveHours > 0) return 'partially-available';
  return 'available';
}

function normalizeChoice<T extends string>(value: string, choices: T[], fallback: T): T {
  return choices.find(choice => choice.toLowerCase() === value.toLowerCase()) || fallback;
}

function getWorkingDates(start: string, end: string): string[] {
  const dates: string[] = [];
  const cursor = new Date(start);
  const last = new Date(end);
  cursor.setUTCHours(12, 0, 0, 0);
  last.setUTCHours(12, 0, 0, 0);

  while (cursor <= last) {
    const day = cursor.getUTCDay();
    if (day !== 0 && day !== 6) dates.push(dateKey(cursor));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return dates;
}

function setting(settings: Record<string, unknown>, key: string): string | null {
  return typeof settings[key] === 'string' ? settings[key] : null;
}

function number(value: string | number | null | undefined, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function round(value: number, decimals = 0): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function dateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function daysBetween(start: string, end: string): number {
  const milliseconds = new Date(end).getTime() - new Date(start).getTime();
  return Math.floor(milliseconds / 86_400_000);
}

function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase();
}

function titleCase(value: string): string {
  return value.replace(/\b\w/g, character => character.toUpperCase());
}

function severityRank(value: string): number {
  return { critical: 4, high: 3, medium: 2, low: 1, info: 0 }[value] ?? 0;
}
