'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { adaptDashboard, mapApiSprint, mapApiTeam, type DashboardView } from '@/lib/api/adapters';
import { getDashboard, getSprints, getSprintTimeline, getTeams } from '@/lib/api/client';
import type { ApiSprint, ApiTeam } from '@/lib/api/types';
import type { Sprint, Team } from '@/types/dashboard';

interface DashboardContextValue {
  teams: Team[];
  sprints: Sprint[];
  selectedTeamId: string | null;
  selectedSprintId: string | null;
  dashboard: DashboardView | null;
  isLoading: boolean;
  error: string | null;
  selectTeam: (teamId: string) => void;
  selectSprint: (sprintId: string) => void;
  refresh: () => void;
}

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [apiTeams, setApiTeams] = useState<ApiTeam[]>([]);
  const [apiSprints, setApiSprints] = useState<ApiSprint[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [selectedSprintId, setSelectedSprintId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardView | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    getTeams(controller.signal)
      .then(page => {
        setApiTeams(page.items);
        setSelectedTeamId(current => {
          if (current && page.items.some(team => team.id === current)) return current;
          return page.items[0]?.id ?? null;
        });
        if (page.items.length === 0) setIsLoading(false);
      })
      .catch(requestError => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setError(messageFrom(requestError));
        setIsLoading(false);
      });

    return () => controller.abort();
  }, [refreshKey]);

  useEffect(() => {
    if (!selectedTeamId) return;

    const controller = new AbortController();

    getSprints(selectedTeamId, controller.signal)
      .then(page => {
        setApiSprints(page.items);
        setSelectedSprintId(current => {
          if (current && page.items.some(sprint => sprint.id === current)) return current;
          return page.items.find(sprint => sprint.state === 'active')?.id ?? page.items[0]?.id ?? null;
        });
        if (page.items.length === 0) setIsLoading(false);
      })
      .catch(requestError => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setError(messageFrom(requestError));
        setIsLoading(false);
      });

    return () => controller.abort();
  }, [refreshKey, selectedTeamId]);

  useEffect(() => {
    if (!selectedTeamId || !selectedSprintId) return;

    const controller = new AbortController();

    Promise.all([
      getDashboard(selectedTeamId, selectedSprintId, controller.signal),
      getSprintTimeline(selectedSprintId, controller.signal),
    ])
      .then(([dashboardResponse, timeline]) => {
        setDashboard(adaptDashboard(dashboardResponse, timeline));
        setIsLoading(false);
      })
      .catch(requestError => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setError(messageFrom(requestError));
        setIsLoading(false);
      });

    return () => controller.abort();
  }, [refreshKey, selectedSprintId, selectedTeamId]);

  const selectTeam = useCallback((teamId: string) => {
    setApiSprints([]);
    setSelectedTeamId(teamId);
    setSelectedSprintId(null);
    setDashboard(null);
    setError(null);
    setIsLoading(true);
  }, []);
  const selectSprint = useCallback((sprintId: string) => {
    setSelectedSprintId(sprintId);
    setDashboard(null);
    setError(null);
    setIsLoading(true);
  }, []);
  const refresh = useCallback(() => {
    setError(null);
    setIsLoading(true);
    setRefreshKey(current => current + 1);
  }, []);

  const value = useMemo<DashboardContextValue>(() => ({
    teams: apiTeams.map(mapApiTeam),
    sprints: apiSprints.map(sprint => mapApiSprint(sprint)),
    selectedTeamId,
    selectedSprintId,
    dashboard,
    isLoading,
    error,
    selectTeam,
    selectSprint,
    refresh,
  }), [
    apiSprints,
    apiTeams,
    dashboard,
    error,
    isLoading,
    refresh,
    selectSprint,
    selectTeam,
    selectedSprintId,
    selectedTeamId,
  ]);

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) throw new Error('useDashboard must be used inside DashboardProvider');
  return context;
}

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : 'Unable to load capacity planning data.';
}
