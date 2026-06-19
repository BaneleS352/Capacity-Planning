import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatShortDate, formatStoryPoints } from '@/lib/formatters';
import type { ScopeChange } from '@/types/sprint';
import styles from './ScopeChangePanel.module.css';

interface ScopeChangePanelProps {
  changes: ScopeChange[];
}

const CHANGE_COLOURS = {
  added: 'blue',
  removed: 'green',
  're-estimated': 'amber',
} as const;

export function ScopeChangePanel({ changes }: ScopeChangePanelProps) {
  const sortedChanges = [...changes].sort((a, b) => a.dayNumber - b.dayNumber);
  const netPoints = changes.reduce((total, change) => total + change.storyPoints, 0);

  return (
    <Card>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Scope Changes</h2>
            <p className={styles.subtitle}>Net change {formatStoryPoints(netPoints)}</p>
          </div>
          <Badge variant={netPoints > 0 ? 'amber' : 'green'}>{changes.length} changes</Badge>
        </div>

        <div className={styles.timeline}>
          {sortedChanges.map(change => (
            <div key={change.id} className={styles.timelineItem}>
              <span className={styles.timelineDot} />
              <span className={styles.timelineLine} />
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <span className={styles.dayLabel}>Day {change.dayNumber}</span>
                  <span className={styles.dateLabel}>{formatShortDate(change.date)}</span>
                  <Badge variant={CHANGE_COLOURS[change.type]}>{change.type}</Badge>
                  <span className={styles.pointsLabel}>
                    {change.storyPoints > 0 ? '+' : ''}{formatStoryPoints(change.storyPoints)}
                  </span>
                </div>
                <h3 className={styles.issueTitle}>{change.issueKey}: {change.issueTitle}</h3>
                <p className={styles.issueReason}>{change.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
