'use client';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useDashboard } from '@/contexts/DashboardContext';
import { formatDateTime } from '@/lib/formatters';

export default function AdminPage() {
  const { dashboard, error, isLoading } = useDashboard();
  const freshness = dashboard?.data.dataFreshness;
  const integrations = freshness ? [
    { name: 'Jira Cloud', source: 'jira', syncedAt: freshness.jiraLastSyncedAt },
    { name: 'PaySpace', source: 'payspace', syncedAt: freshness.payspaceLastSyncedAt },
    { name: 'Capacity Rules', source: 'capacity', syncedAt: freshness.capacityRecalculatedAt },
  ] : [];

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-6">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Admin</h1>
        <p className="mt-2 text-sm text-text-secondary">Integration and rules status</p>
      </section>

      {!freshness && (
        <EmptyState
          title={isLoading ? 'Loading integration status' : 'Integration status unavailable'}
          description={error || 'Select a team and sprint to inspect data freshness.'}
        />
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {integrations.map(integration => {
          const stale = freshness?.staleSystems.some(item => item.system === integration.source)
            || !integration.syncedAt;
          return (
          <Card key={integration.name}>
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-base font-semibold text-text-primary">{integration.name}</h2>
                <Badge variant={stale ? 'amber' : 'green'}>{stale ? 'Stale' : 'Connected'}</Badge>
              </div>
              <div>
                <div className="text-[11px] font-medium uppercase tracking-wide text-text-tertiary">Last update</div>
                <div className="mt-1 text-sm text-text-secondary">{formatDateTime(integration.syncedAt)}</div>
              </div>
            </div>
          </Card>
          );
        })}
      </div>
    </div>
  );
}
