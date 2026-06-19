import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { riskToColour, utilisationToColour } from '@/lib/statusUtils';
import { formatPercent, formatStoryPoints } from '@/lib/formatters';
import type { ScenarioResult } from '@/types/planning';

interface ScenarioResultsSummaryProps {
  result: ScenarioResult;
}

export function ScenarioResultsSummary({ result }: ScenarioResultsSummaryProps) {
  const riskColour = riskToColour(result.adjustedRiskLevel);
  const utilisationColour = utilisationToColour(result.adjustedUtilisationPercent);

  return (
    <section className="rounded-lg border border-border bg-white">
      <div className="border-b border-border p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">Scenario Result</h2>
            <p className="mt-1 text-sm text-text-secondary">Recalculated sprint position</p>
          </div>
          <Badge variant={riskColour}>{result.adjustedRiskLevel}</Badge>
        </div>
      </div>

      <div className="space-y-5 p-4">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-text-primary">Adjusted utilisation</span>
            <span className="text-sm font-semibold text-text-primary">
              {formatPercent(result.adjustedUtilisationPercent)}
            </span>
          </div>
          <ProgressBar
            value={result.adjustedUtilisationPercent}
            colour={utilisationColour === 'red' ? 'red' : utilisationColour === 'amber' ? 'amber' : 'green'}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <ResultMetric label="Capacity" value={`${result.adjustedCapacityPersonDays} pd`} />
          <ResultMetric label="Committed" value={formatStoryPoints(result.adjustedCommittedPoints)} />
          <ResultMetric label="Target load" value={formatStoryPoints(result.recommendedLoad)} />
          <ResultMetric label="Constraint" value={result.constrainedRole ?? 'None'} />
        </div>

        <div className="rounded-lg border border-blue-100 bg-blue-50 px-3 py-3">
          <div className="text-[11px] font-medium uppercase tracking-wide text-blue-600">Recommended action</div>
          <p className="mt-1 text-sm leading-relaxed text-blue-800">{result.suggestedAction}</p>
        </div>
      </div>
    </section>
  );
}

function ResultMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-sunken px-3 py-3">
      <div className="text-[11px] font-medium uppercase tracking-wide text-text-tertiary">{label}</div>
      <div className="mt-1 text-sm font-semibold text-text-primary">{value}</div>
    </div>
  );
}
