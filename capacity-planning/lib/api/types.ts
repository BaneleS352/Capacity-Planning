export interface ApiPage<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiTeam {
  id: string;
  name: string;
  slug: string;
  department: string | null;
  timezone: string;
  location_code: string | null;
  working_hours_per_day: string;
  settings: Record<string, unknown>;
}

export interface ApiSprint {
  id: string;
  team_id: string;
  name: string;
  state: string;
  start_at: string;
  end_at: string;
  completed_at: string | null;
  goal: string | null;
}

export interface ApiEmployee {
  id: string;
  organization_id: string;
  payspace_employee_number: string | null;
  jira_account_id: string | null;
  corporate_email: string;
  full_name: string;
  role_name: string;
  department: string | null;
  manager_employee_id: string | null;
  employment_type: string;
  location_code: string | null;
  contract_hours_per_day: string;
  fte_factor: string;
  active: boolean;
  source_updated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiMembership {
  id: string;
  team_id: string;
  employee_id: string;
  allocation_percent: string;
  delivery_role: string | null;
  critical_role: boolean;
}

export interface ApiEmployeeCapacity {
  id: string;
  sprint_id: string;
  employee_id: string;
  calculated_at: string;
  working_days: string;
  gross_hours: string;
  leave_hours: string;
  holiday_hours: string;
  ceremony_hours: string;
  buffer_hours: string;
  net_hours: string;
  effective_person_days: string;
  assigned_story_points: string;
  inputs: Record<string, unknown>;
}

export interface ApiTeamCapacity {
  calculated_at: string;
  effective_person_days: string;
  leave_impact_hours: string;
  story_points_per_effective_day: string | null;
  story_point_capacity: string | null;
  committed_story_points: string;
  added_story_points: string;
  removed_story_points: string;
  completed_story_points: string;
  in_progress_story_points: string;
  remaining_story_points: string;
  utilization_percent: string | null;
  risk_level: string;
}

export interface ApiJiraIssue {
  id: string;
  issue_key: string;
  summary: string;
  assignee_employee_id: string | null;
  status: string;
  status_category: string;
  priority: string | null;
  issue_type: string | null;
  epic_key: string | null;
  story_points: string;
  blocked: boolean;
  blocked_since: string | null;
  flagged: boolean;
  added_to_sprint_at: string | null;
  removed_from_sprint_at: string | null;
  completed_at: string | null;
  source_updated_at: string;
  normalized_fields: Record<string, unknown>;
}

export interface ApiRisk {
  id: string;
  risk_type: string;
  severity: string;
  message: string;
  recommendation: string | null;
  context: Record<string, unknown>;
}

export interface ApiFreshness {
  jira_last_synced_at: string | null;
  payspace_last_synced_at: string | null;
  capacity_calculated_at: string | null;
  stale_sources: string[];
}

export interface ApiDashboardMember {
  employee: ApiEmployee;
  membership: ApiMembership;
  capacity: ApiEmployeeCapacity | null;
}

export interface ApiTeamDashboard {
  team: ApiTeam;
  sprint: ApiSprint;
  capacity: ApiTeamCapacity | null;
  members: ApiDashboardMember[];
  issues: ApiJiraIssue[];
  risks: ApiRisk[];
  freshness: ApiFreshness;
}

export interface ApiSprintSnapshot {
  id: string;
  captured_at: string;
  committed_story_points: string;
  added_story_points: string;
  removed_story_points: string;
  completed_story_points: string;
}

export interface ApiSprintTimeline {
  sprint: ApiSprint;
  snapshots: ApiSprintSnapshot[];
  issues: ApiJiraIssue[];
}

export interface ApiPlannedVsActual {
  sprint_id: string;
  sprint_name: string;
  committed_story_points: string;
  added_story_points: string;
  removed_story_points: string;
  completed_story_points: string;
  carry_over_story_points: string;
  delivery_percent: string | null;
}

export interface ApiLeave {
  id: string;
  employee_id: string;
  start_date: string;
  end_date: string;
  leave_type: string;
  reason: string | null;
  partial_day_hours: string | null;
  status: string;
  source_reference_id: string;
  source_updated_at: string | null;
}

export interface ApiEmployeeStoryPointsHistory {
  sprint_id: string;
  sprint_name: string;
  end_at: string;
  assigned_story_points: string;
  completed_story_points: string;
  completed_issue_count: number;
}

export interface ApiEmployeeProfile {
  employee: ApiEmployee;
  memberships: ApiMembership[];
  current_capacity: ApiEmployeeCapacity | null;
  current_issues: ApiJiraIssue[];
  completed_issues: ApiJiraIssue[];
  leave: ApiLeave[];
  historical_capacity: ApiEmployeeCapacity[];
  story_points_history: ApiEmployeeStoryPointsHistory[];
}
