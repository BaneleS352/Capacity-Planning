import type { DataFreshness } from '@/types/dashboard';
import { formatTime } from '@/lib/formatters';
import { StatusDot } from '@/components/ui/StatusDot';
import styles from './DataFreshnessIndicator.module.css';

interface DataFreshnessIndicatorProps {
  freshness: DataFreshness;
}

export function DataFreshnessIndicator({ freshness }: DataFreshnessIndicatorProps) {
  const hasStale = freshness.staleSystems.length > 0;

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Data Freshness</h3>
      <div className={styles.rowList}>
        <FreshnessRow label="Jira synced" time={formatTime(freshness.jiraLastSyncedAt)} fresh={!freshness.staleSystems.some(item => item.system === 'jira')} />
        <FreshnessRow label="PaySpace synced" time={formatTime(freshness.payspaceLastSyncedAt)} fresh={!freshness.staleSystems.some(item => item.system === 'payspace')} />
        <FreshnessRow label="Capacity recalculated" time={formatTime(freshness.capacityRecalculatedAt)} fresh={Boolean(freshness.capacityRecalculatedAt)} />
      </div>
      {hasStale && (
        <div className={styles.staleAlert}>
          {freshness.staleSystems.map(s => (
            <p key={s.system} className={styles.staleMessage}>{s.message}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function FreshnessRow({ label, time, fresh }: { label: string; time: string; fresh: boolean }) {
  return (
    <div className={styles.row}>
      <StatusDot colour={fresh ? 'green' : 'amber'} />
      <span className={styles.rowLabel}>{label}</span>
      <span className={styles.rowTime}>{time}</span>
    </div>
  );
}
