'use client';

import { useState } from 'react';
import { GlobalNavigation } from './GlobalNavigation';
import { DashboardTopBar } from './DashboardTopBar';
import { DashboardProvider } from '@/contexts/DashboardContext';
import styles from './AppShell.module.css';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <DashboardProvider>
    <div className={styles.appShell}>
      {/* Mobile overlay */}
      <div
        className={`${styles.mobileOverlay} ${mobileOpen ? styles.isOpen : ''}`}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        className={`${styles.sidebar} ${collapsed ? styles.isCollapsed : ''} ${
          mobileOpen ? styles.isMobileOpen : ''
        }`}
      >
        <GlobalNavigation
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
          onMobileClose={() => setMobileOpen(false)}
        />
      </aside>

      {/* Main content */}
      <div className={styles.mainContent}>
        <DashboardTopBar onMenuClick={() => setMobileOpen(true)} />
        <main className={styles.mainArea}>
          {children}
        </main>
      </div>
    </div>
    </DashboardProvider>
  );
}
