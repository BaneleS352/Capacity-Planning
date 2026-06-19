import type { StatusColour } from '@/constants/statusColours';
import styles from './StatusDot.module.css';

interface StatusDotProps {
  colour: StatusColour;
  pulse?: boolean;
}

export function StatusDot({ colour, pulse = false }: StatusDotProps) {
  const colourClass = {
    green: styles.variantGreen,
    amber: styles.variantAmber,
    red: styles.variantRed,
    blue: styles.variantBlue,
    grey: styles.variantGrey,
  }[colour];

  return (
    <span className={styles.container}>
      {pulse && (
        <span className={`${styles.pulse} ${colourClass}`} />
      )}
      <span className={`${styles.dot} ${colourClass}`} />
    </span>
  );
}
