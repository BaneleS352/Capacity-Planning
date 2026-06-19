'use client';

import styles from './Tooltip.module.css';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const positionClass = {
    top: styles.positionTop,
    bottom: styles.positionBottom,
    left: styles.positionLeft,
    right: styles.positionRight,
  }[position];

  const arrowClass = {
    top: styles.arrowTop,
    bottom: styles.arrowBottom,
    left: styles.arrowLeft,
    right: styles.arrowRight,
  }[position];

  return (
    <div className={styles.wrapper}>
      {children}
      <div
        role="tooltip"
        className={`${styles.tooltip} ${positionClass}`}
      >
        <div className={styles.content}>
          {content}
          <span className={`${styles.arrow} ${arrowClass}`} />
        </div>
      </div>
    </div>
  );
}
