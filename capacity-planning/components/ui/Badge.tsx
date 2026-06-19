'use client';

import type { StatusColour } from '@/constants/statusColours';
import styles from './Badge.module.css';

interface BadgeProps {
  variant: StatusColour;
  children: React.ReactNode;
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({ variant, children, size = 'sm', className = '' }: BadgeProps) {
  const variantClass = {
    green: styles.variantGreen,
    amber: styles.variantAmber,
    red: styles.variantRed,
    blue: styles.variantBlue,
    grey: styles.variantGrey,
  }[variant];

  const sizeClass = size === 'sm' ? styles.sizeSm : styles.sizeMd;

  return (
    <span className={`${styles.badge} ${variantClass} ${sizeClass} ${className}`}>
      {children}
    </span>
  );
}
