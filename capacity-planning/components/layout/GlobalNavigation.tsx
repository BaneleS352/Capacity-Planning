'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MAIN_NAV_ITEMS, PRODUCT_NAME, PRODUCT_SUBTITLE, SECONDARY_NAV_ITEMS } from '@/constants/navigation';
import styles from './GlobalNavigation.module.css';

interface GlobalNavigationProps {
  collapsed: boolean;
  onToggle: () => void;
  onMobileClose?: () => void;
}

const NAV_ICONS: Record<string, React.ReactNode> = {
  grid: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="6" height="6" rx="1" />
      <rect x="11" y="3" width="6" height="6" rx="1" />
      <rect x="3" y="11" width="6" height="6" rx="1" />
      <rect x="11" y="11" width="6" height="6" rx="1" />
    </svg>
  ),
  sliders: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <line x1="4" y1="16" x2="4" y2="4" /><circle cx="4" cy="8" r="2" fill="currentColor" />
      <line x1="10" y1="16" x2="10" y2="4" /><circle cx="10" cy="13" r="2" fill="currentColor" />
      <line x1="16" y1="16" x2="16" y2="4" /><circle cx="16" cy="6" r="2" fill="currentColor" />
    </svg>
  ),
  users: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="7" cy="7" r="3" /><path d="M2 17c0-3 2.5-5 5-5s5 2 5 5" />
      <circle cx="14" cy="6" r="2" /><path d="M14 11c2 0 4 1.5 4 4" />
    </svg>
  ),
  layers: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 3 3 6.5 10 10l7-3.5L10 3z" />
      <path d="m3 10 7 3.5 7-3.5" />
      <path d="m3 13.5 7 3.5 7-3.5" />
    </svg>
  ),
  'bar-chart': (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="10" width="3" height="7" rx="0.5" /><rect x="8.5" y="5" width="3" height="12" rx="0.5" /><rect x="14" y="8" width="3" height="9" rx="0.5" />
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="10" r="2.5" /><path d="M10 2v2m0 12v2m-6.93-3.07 1.41-1.41m9.9-9.9 1.41-1.41M2 10h2m12 0h2m-3.07 6.93-1.41-1.41M5.48 5.48 4.07 4.07" />
    </svg>
  ),
  link: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.5 11.5 11.5 8.5" />
      <path d="M7.5 7.5 6.25 6.25a3 3 0 0 0-4.25 4.25l1.5 1.5a3 3 0 0 0 4.25 0" />
      <path d="m12.5 12.5 1.25 1.25A3 3 0 0 0 18 9.5L16.5 8a3 3 0 0 0-4.25 0" />
    </svg>
  ),
};

function NavLink({
  item,
  collapsed,
  active,
  onClick,
}: {
  item: { href: string; label: string; icon: string };
  collapsed: boolean;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Link
      key={item.href}
      href={item.href}
      onClick={onClick}
      className={`${styles.navLink} ${active ? styles.active : ''} ${collapsed ? styles.collapsed : ''} focus-ring`}
      title={collapsed ? item.label : undefined}
    >
      <span className={styles.iconWrapper}>{NAV_ICONS[item.icon] || NAV_ICONS.grid}</span>
      {!collapsed && <span className={styles.linkLabel}>{item.label}</span>}
    </Link>
  );
}

export function GlobalNavigation({ collapsed, onToggle, onMobileClose }: GlobalNavigationProps) {
  const pathname = usePathname();

  const handleLinkClick = () => {
    onMobileClose?.();
  };

  return (
    <div className={styles.navContainer}>
      {/* Logo area */}
      <div className={styles.logoArea}>
        <div className={styles.logoIcon}>
          CP
        </div>
        {!collapsed && (
          <div className={styles.logoTextContainer}>
            <div className={styles.logoTitle}>{PRODUCT_NAME}</div>
            <div className={styles.logoSubtitle}>{PRODUCT_SUBTITLE}</div>
          </div>
        )}
      </div>

      {/* Nav items */}
      <nav className={styles.navSection}>
        {MAIN_NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <NavLink
              key={item.href}
              item={item}
              collapsed={collapsed}
              active={isActive}
              onClick={handleLinkClick}
            />
          );
        })}
      </nav>

      <nav className={styles.secondaryNav}>
        {SECONDARY_NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <NavLink
              key={item.href}
              item={item}
              collapsed={collapsed}
              active={isActive}
              onClick={handleLinkClick}
            />
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className={styles.collapseContainer}>
        <button
          onClick={onToggle}
          className={`${styles.collapseButton} focus-ring`}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <svg
            width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            className={`${styles.collapseIcon} ${collapsed ? styles.rotated : ''}`}
          >
            <path d="M10 3L5 8l5 5" />
          </svg>
        </button>
      </div>
    </div>
  );
}
