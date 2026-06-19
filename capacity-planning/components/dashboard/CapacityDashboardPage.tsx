'use client';

import { useDashboard } from '@/contexts/DashboardContext';
import { Card } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { SprintHealthHero } from './SprintHealthHero';
import { CapacitySummaryGrid } from './CapacitySummaryGrid';
import { RiskInsightPanel } from './RiskInsightPanel';
import { DataFreshnessIndicator } from './DataFreshnessIndicator';
import { TeamMemberCapacityTable } from './TeamMemberCapacityTable';
import { AvailabilityHeatmap } from './AvailabilityHeatmap';
import { SprintWorkloadPanel } from './SprintWorkloadPanel';
import { LeaveImpactPanel } from './LeaveImpactPanel';
import { ScopeChangePanel } from './ScopeChangePanel';
import { SprintBurndownChart } from './SprintBurndownChart';
import { WorkloadDistributionChart } from './WorkloadDistributionChart';
import styles from './CapacityDashboardPage.module.css';

export function CapacityDashboardPage() {
  const { dashboard, error, isLoading, refresh, teams, sprints } = useDashboard();

  if (!dashboard) {
    const title = error
      ? 'Could not load the Capacity API'
      : isLoading
        ? 'Loading live capacity data'
        : teams.length === 0
          ? 'No teams found'
          : sprints.length === 0
            ? 'No sprints found for this team'
            : 'No dashboard data available';
    const description = error
      ? `${error} Check CAPACITY_API_URL, CAPACITY_API_TOKEN, and that the FastAPI service is running.`
      : 'The dashboard will appear when API data is available.';

    return (
      <div className={styles.container}>
        <EmptyState title={title} description={description} />
        {error && (
          <button type="button" className={styles.retryButton} onClick={refresh}>
            Retry connection
          </button>
        )}
      </div>
    );
  }

  const { team, sprint, capacitySummary, dataFreshness } = dashboard.data;
  const { members, issues, risks, burndown, scopeChanges } = dashboard;

  return (
    <div className={styles.container}>
      <SprintHealthHero team={team} sprint={sprint} />

      <CapacitySummaryGrid
        summary={capacitySummary}
        riskSignalCount={risks.length}
      />

      <div className={styles.bentoGridLarge}>
        <TeamMemberCapacityTable
          members={members}
          issues={issues}
        />
        <WorkloadDistributionChart members={members} />
      </div>

      <RiskInsightPanel signals={risks} />

      <div className={styles.bentoGridMedium}>
        <SprintWorkloadPanel
          issues={issues}
          members={members}
        />
        <div className={styles.stackedColumn}>
          <LeaveImpactPanel members={members} />
          <Card>
            <DataFreshnessIndicator freshness={dataFreshness} />
          </Card>
        </div>
      </div>

      <div className={styles.bentoGridSmall}>
        <SprintBurndownChart
          sprint={sprint}
          points={burndown}
        />
        <ScopeChangePanel changes={scopeChanges} />
      </div>

      <AvailabilityHeatmap
        members={members}
        sprint={sprint}
      />
    </div>
  );
}
