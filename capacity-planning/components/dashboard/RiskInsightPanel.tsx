import type { RiskSignal } from '@/types/risk';
import { RiskSignalCard } from './RiskSignalCard';
import { sortRisksBySeverity } from '@/lib/riskUtils';
import { Badge } from '@/components/ui/Badge';
import styles from './RiskInsightPanel.module.css';

interface RiskInsightPanelProps {
  signals: RiskSignal[];
}

export function RiskInsightPanel({ signals }: RiskInsightPanelProps) {
  const sorted = sortRisksBySeverity(signals);
  const highCount = signals.filter(s => s.severity === 'high').length;

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.title}>Risk &amp; Recommended Actions</h2>
        <Badge variant={highCount > 0 ? 'red' : 'amber'} size="sm">
          {signals.length} {signals.length === 1 ? 'signal' : 'signals'}
        </Badge>
      </div>
      {sorted.length === 0 ? (
        <p className={styles.emptyState}>No active risk signals.</p>
      ) : (
        <div className={styles.grid}>
          {sorted.map(signal => (
            <RiskSignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}
    </section>
  );
}
