import type { StatusColour } from '@/constants/statusColours';
import styles from './CapacityMetricCard.module.css';

interface CapacityMetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  secondaryText: string;
  riskLevel?: StatusColour;
}

export function CapacityMetricCard({ label, value, unit, secondaryText, riskLevel = 'grey' }: CapacityMetricCardProps) {
  const accentClass = {
    green: styles.accentGreen,
    amber: styles.accentAmber,
    red: styles.accentRed,
    blue: styles.accentBlue,
    grey: styles.accentGrey,
  }[riskLevel];

  return (
    <div className={`${styles.card} ${accentClass}`}>
      <div className={styles.label}>{label}</div>
      <div className={styles.valueContainer}>
        <span className={styles.value}>{value}</span>
        {unit && <span className={styles.unit}>{unit}</span>}
      </div>
      <div className={styles.secondaryText}>{secondaryText}</div>
    </div>
  );
}
