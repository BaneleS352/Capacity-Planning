'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useDashboard } from '@/contexts/DashboardContext';
import { getPlannedVsActual } from '@/lib/api/client';
import type { ApiPlannedVsActual } from '@/lib/api/types';

export default function ReportsPage() {
  const { selectedTeamId, dashboard } = useDashboard();
  const [reportState, setReportState] = useState<{
    teamId: string | null;
    reports: ApiPlannedVsActual[];
    error: string | null;
  }>({ teamId: null, reports: [], error: null });

  useEffect(() => {
    if (!selectedTeamId) return;
    const controller = new AbortController();
    getPlannedVsActual(selectedTeamId, controller.signal)
      .then(reports => setReportState({ teamId: selectedTeamId, reports, error: null }))
      .catch(requestError => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setReportState({
          teamId: selectedTeamId,
          reports: [],
          error: requestError instanceof Error ? requestError.message : 'Unable to load reports.',
        });
      });
    return () => controller.abort();
  }, [selectedTeamId]);

  const reports = reportState.teamId === selectedTeamId ? reportState.reports : [];
  const error = reportState.teamId === selectedTeamId ? reportState.error : null;

  const latest = reports[0];
  const metrics = latest ? [
    {
      category: 'Delivery',
      planned: number(latest.committed_story_points),
      actual: number(latest.completed_story_points),
    },
    {
      category: 'Current scope',
      planned: number(latest.committed_story_points),
      actual: number(latest.committed_story_points) + number(latest.added_story_points) - number(latest.removed_story_points),
    },
    {
      category: 'Carry-over',
      planned: 0,
      actual: number(latest.carry_over_story_points),
    },
  ] : [];

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-6">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Reports</h1>
        <p className="mt-2 text-sm text-text-secondary">
          {latest?.sprint_name || dashboard?.data.sprint.name || 'Selected team'} delivery signals
        </p>
      </section>

      {!latest && (
        <EmptyState
          title={error ? 'Could not load reports' : 'No calculated sprint reports'}
          description={error || 'Reports appear after capacity has been calculated for a sprint.'}
        />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {metrics.map(item => {
          const variance = item.actual - item.planned;
          return (
            <Card key={item.category}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[11px] font-medium uppercase tracking-wide text-text-tertiary">{item.category}</div>
                  <div className="mt-2 text-2xl font-semibold text-text-primary">{item.actual}</div>
                  <div className="mt-1 text-sm text-text-secondary">Planned {item.planned}</div>
                </div>
                <Badge variant={item.category === 'Delivery' && variance >= 0 ? 'green' : variance === 0 ? 'green' : 'amber'}>
                  {variance > 0 ? '+' : ''}{variance}
                </Badge>
              </div>
            </Card>
          );
        })}
      </div>

      {reports.length > 0 && (
        <Card>
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-text-primary">Delivery Trend</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[...reports].reverse().slice(-8).map(point => {
                const value = number(point.delivery_percent);
                return (
                  <div key={point.sprint_id} className="space-y-2">
                    <div className="flex h-28 items-end rounded-lg bg-surface-sunken px-4">
                      <div className="w-full rounded-t-md bg-accent" style={{ height: `${Math.min(value, 100)}%` }} />
                    </div>
                    <div className="text-center text-xs font-medium text-text-secondary">
                      {point.sprint_name} / {value}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function number(value: string | null): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}
