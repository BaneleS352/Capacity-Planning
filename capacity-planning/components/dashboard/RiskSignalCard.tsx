import type { RiskSignal } from '@/types/risk';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { riskToColour } from '@/lib/statusUtils';
import styles from './RiskSignalCard.module.css';

interface RiskSignalCardProps {
  signal: RiskSignal;
}

export function RiskSignalCard({ signal }: RiskSignalCardProps) {
  const colour = riskToColour(signal.severity);
  const borderAccent: Record<string, string> = {
    red: styles.accentRed,
    amber: styles.accentAmber,
    green: styles.accentGreen,
  };

  return (
    <Card className={`${styles.cardWrapper} ${borderAccent[colour] || ''}`}>
      <div className={styles.content}>
        <div className={styles.header}>
          <Badge variant={colour} size="sm">
            {signal.severity.charAt(0).toUpperCase() + signal.severity.slice(1)}
          </Badge>
          <span className={styles.typeLabel}>{signal.type.replace(/-/g, ' ')}</span>
        </div>

        <h3 className={styles.title}>{signal.title}</h3>

        <div>
          <div className={styles.sectionTitle}>Why it matters</div>
          <p className={styles.textBlock}>{signal.whyItMatters}</p>
        </div>

        {signal.contributingFactors.length > 0 && (
          <div>
            <div className={styles.sectionTitle}>Contributing factors</div>
            <ul className={styles.factorsList}>
              {signal.contributingFactors.map((f, i) => (
                <li key={i} className={styles.factorItem}>
                  <span className={styles.bullet}>•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className={styles.recommendationBox}>
          <div className={styles.recommendationTitle}>Recommended action</div>
          <p className={styles.recommendationText}>{signal.recommendation}</p>
        </div>
      </div>
    </Card>
  );
}
