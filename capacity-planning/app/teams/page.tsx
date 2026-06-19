'use client';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useDashboard } from '@/contexts/DashboardContext';

export default function TeamsPage() {
  const { teams, isLoading, error } = useDashboard();

  return (
    <div className="mx-auto flex w-full max-w-[1180px] flex-col gap-6">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Teams</h1>
        <p className="mt-2 text-sm text-text-secondary">Engineering capacity groups</p>
      </section>

      {teams.length === 0 && (
        <EmptyState
          title={isLoading ? 'Loading teams' : 'No teams available'}
          description={error || 'Create a team through the Capacity API to see it here.'}
        />
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {teams.map(team => (
          <Card key={team.id} hover>
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold text-text-primary">{team.name}</h2>
                  <p className="mt-1 text-sm text-text-secondary">{team.department}</p>
                </div>
                {team.isFavourite && <Badge variant="amber">Primary</Badge>}
              </div>

              <dl className="grid grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-[10px] font-medium uppercase tracking-wide text-text-tertiary">EM</dt>
                  <dd className="mt-1 font-medium text-text-primary">{team.engineeringManager}</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-medium uppercase tracking-wide text-text-tertiary">SM</dt>
                  <dd className="mt-1 font-medium text-text-primary">{team.scrumMaster}</dd>
                </div>
                <div>
                  <dt className="text-[10px] font-medium uppercase tracking-wide text-text-tertiary">PO</dt>
                  <dd className="mt-1 font-medium text-text-primary">{team.productOwner}</dd>
                </div>
              </dl>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
