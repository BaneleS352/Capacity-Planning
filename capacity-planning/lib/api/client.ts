import type {
  ApiPage,
  ApiEmployeeProfile,
  ApiPlannedVsActual,
  ApiSprint,
  ApiSprintTimeline,
  ApiTeam,
  ApiTeamDashboard,
} from './types';

interface ProblemDetails {
  detail?: string;
  title?: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/backend${path}`, {
    signal,
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  });

  if (!response.ok) {
    let problem: ProblemDetails = {};
    try {
      problem = await response.json() as ProblemDetails;
    } catch {
      // The status text remains useful when an upstream response is not JSON.
    }
    throw new ApiError(
      problem.detail || problem.title || response.statusText || 'API request failed',
      response.status,
    );
  }

  return response.json() as Promise<T>;
}

export function getTeams(signal?: AbortSignal) {
  return apiGet<ApiPage<ApiTeam>>('/teams?page_size=200', signal);
}

export function getSprints(teamId: string, signal?: AbortSignal) {
  const query = new URLSearchParams({ team_id: teamId, page_size: '200' });
  return apiGet<ApiPage<ApiSprint>>(`/sprints?${query}`, signal);
}

export function getDashboard(teamId: string, sprintId: string, signal?: AbortSignal) {
  const query = new URLSearchParams({ sprint_id: sprintId });
  return apiGet<ApiTeamDashboard>(`/teams/${teamId}/dashboard?${query}`, signal);
}

export function getSprintTimeline(sprintId: string, signal?: AbortSignal) {
  return apiGet<ApiSprintTimeline>(`/sprints/${sprintId}/timeline`, signal);
}

export function getPlannedVsActual(teamId: string, signal?: AbortSignal) {
  const query = new URLSearchParams({ team_id: teamId, limit: '12' });
  return apiGet<ApiPlannedVsActual[]>(`/reports/planned-vs-actual?${query}`, signal);
}

export function getEmployeeProfile(employeeId: string, signal?: AbortSignal) {
  return apiGet<ApiEmployeeProfile>(`/employees/${employeeId}/profile`, signal);
}
