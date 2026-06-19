'use client';

import { ScenarioAssumptionsForm } from './ScenarioAssumptionsForm';
import { ScenarioResultsSummary } from './ScenarioResultsSummary';
import { usePlanningScenario } from '@/hooks/usePlanningScenario';
import { EmptyState } from '@/components/ui/EmptyState';
import { useDashboard } from '@/contexts/DashboardContext';

export function PlanningScenarioPanel() {
  const { dashboard, error, isLoading } = useDashboard();

  if (!dashboard) {
    return (
      <EmptyState
        title={isLoading ? 'Loading planning baseline' : 'Planning baseline unavailable'}
        description={error || 'Select a team and sprint with calculated capacity.'}
      />
    );
  }

  return <PlanningScenarioContent capacitySummary={dashboard.data.capacitySummary} />;
}

function PlanningScenarioContent({ capacitySummary }: { capacitySummary: import('@/types/dashboard').CapacitySummary }) {
  const { scenario, updateAssumption, resetScenario } = usePlanningScenario(capacitySummary);

  return (
    <div className="mx-auto flex w-full max-w-[1280px] flex-col gap-6">
      <section className="rounded-lg border border-border bg-white p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-text-primary">Planning</h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-text-secondary">
              {scenario.name}
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <BaselineMetric label="Current capacity" value={`${capacitySummary.availablePersonDays} pd`} />
            <BaselineMetric label="Current scope" value={`${capacitySummary.committedStoryPointEquivalent} SP`} />
            <BaselineMetric label="Current utilisation" value={`${capacitySummary.utilisationPercent}%`} />
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(360px,0.65fr)]">
        <ScenarioAssumptionsForm
          assumptions={scenario.assumptions}
          onChange={updateAssumption}
          onReset={resetScenario}
        />
        <ScenarioResultsSummary result={scenario.result} />
      </div>
    </div>
  );
}

function BaselineMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-28 rounded-lg border border-border bg-surface-sunken px-3 py-2">
      <div className="text-[10px] font-medium uppercase tracking-wide text-text-tertiary">{label}</div>
      <div className="mt-1 text-sm font-semibold text-text-primary">{value}</div>
    </div>
  );
}
