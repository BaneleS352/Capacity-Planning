import type { CapacitySummary } from '@/types/dashboard';
import { CapacityMetricCard } from './CapacityMetricCard';
import { utilisationToColour, riskToColour } from '@/lib/statusUtils';
import { formatPercent } from '@/lib/formatters';
import { UTILISATION_THRESHOLDS } from '@/constants/capacityThresholds';
import styles from './CapacitySummaryGrid.module.css';

interface CapacitySummaryGridProps {
  summary: CapacitySummary;
  riskSignalCount?: number;
}

export function CapacitySummaryGrid({ summary, riskSignalCount = 0 }: CapacitySummaryGridProps) {
  const utilLabel = summary.utilisationPercent <= UTILISATION_THRESHOLDS.HEALTHY_MAX ? 'Healthy'
    : summary.utilisationPercent <= UTILISATION_THRESHOLDS.WATCH_MAX ? 'Moderate' : 'High';

  return (
    <div className={styles.grid}>
      <CapacityMetricCard
        label="Available Capacity"
        value={summary.availablePersonDays}
        unit="person-days"
        secondaryText="Adjusted for leave and ceremonies"
        riskLevel="blue"
      />
      <CapacityMetricCard
        label="Committed Work"
        value={summary.committedStoryPointEquivalent}
        unit="SP equivalent"
        secondaryText="Total planned sprint workload"
        riskLevel={utilisationToColour(summary.utilisationPercent)}
      />
      <CapacityMetricCard
        label="Utilisation"
        value={formatPercent(summary.utilisationPercent)}
        secondaryText={utilLabel}
        riskLevel={utilisationToColour(summary.utilisationPercent)}
      />
      <CapacityMetricCard
        label="Risk Level"
        value={summary.riskLevel.charAt(0).toUpperCase() + summary.riskLevel.slice(1)}
        secondaryText={`${riskSignalCount} active signals`}
        riskLevel={riskToColour(summary.riskLevel)}
      />
      <CapacityMetricCard
        label="Completed"
        value={summary.completedStoryPoints}
        unit="SP"
        secondaryText="Done this sprint"
        riskLevel="green"
      />
      <CapacityMetricCard
        label="In Progress"
        value={summary.inProgressStoryPoints}
        unit="SP"
        secondaryText="Currently being worked on"
        riskLevel="blue"
      />
      <CapacityMetricCard
        label="Remaining"
        value={summary.remainingStoryPoints}
        unit="SP"
        secondaryText="Yet to be started"
        riskLevel={summary.remainingStoryPoints > summary.completedStoryPoints ? 'amber' : 'grey'}
      />
      <CapacityMetricCard
        label="Leave Impact"
        value={`-${summary.leaveImpactPersonDays}`}
        unit="person-days"
        secondaryText="Capacity lost to leave"
        riskLevel="amber"
      />
    </div>
  );
}
