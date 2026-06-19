import styles from './Card.module.css';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export function Card({ children, className = '', padding = 'md', hover = false }: CardProps) {
  const paddingClass = {
    sm: styles.paddingSm,
    md: styles.paddingMd,
    lg: styles.paddingLg,
  }[padding];

  return (
    <div
      className={`${styles.card} ${paddingClass} ${hover ? styles.hoverable : ''} ${className}`}
    >
      {children}
    </div>
  );
}
