import styles from './ProgressBar.module.css';

interface ProgressBarProps {
  value: number;
  colour?: 'green' | 'amber' | 'red';
  label?: string;
  showPercent?: boolean;
}

export function ProgressBar({
  value,
  colour = 'green',
  label,
  showPercent = false,
}: ProgressBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value));

  const colourClass = {
    green: styles.variantGreen,
    amber: styles.variantAmber,
    red: styles.variantRed,
  }[colour];

  return (
    <div className={styles.container}>
      {(label || showPercent) && (
        <div className={styles.header}>
          {label && (
            <span className={styles.label}>{label}</span>
          )}
          {showPercent && (
            <span className={styles.percent}>
              {Math.round(clampedValue)}%
            </span>
          )}
        </div>
      )}
      <div className={styles.track}>
        <div
          className={`${styles.bar} ${colourClass}`}
          style={{ width: `${clampedValue}%` }}
          role="progressbar"
          aria-valuenow={clampedValue}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
