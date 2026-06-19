'use client';

import { TeamMemberCapacityTable } from '@/components/dashboard/TeamMemberCapacityTable';
import { EmptyState } from '@/components/ui/EmptyState';
import { useDashboard } from '@/contexts/DashboardContext';

export default function EmployeesPage() {
  const { dashboard, error, isLoading } = useDashboard();

  return (
    <div className="mx-auto flex w-full max-w-[1280px] flex-col gap-6">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Employees</h1>
        <p className="mt-2 text-sm text-text-secondary">
          {dashboard ? `${dashboard.data.team.name} capacity roster` : 'Selected team capacity roster'}
        </p>
      </section>
      {dashboard ? (
        <TeamMemberCapacityTable members={dashboard.members} issues={dashboard.issues} />
      ) : (
        <EmptyState
          title={isLoading ? 'Loading employees' : 'Employee data unavailable'}
          description={error || 'Select a team with an active sprint to view its roster.'}
        />
      )}
    </div>
  );
}
