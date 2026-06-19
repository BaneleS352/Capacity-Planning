'use client';

import { useState } from 'react';
import { EmployeeProfileDrawer } from '@/components/employees/EmployeeProfileDrawer';
import { useDashboard } from '@/contexts/DashboardContext';
import { useEmployeeDrawer } from '@/hooks/useEmployeeDrawer';
import { formatTime } from '@/lib/formatters';
import { TeamSwitcher } from './TeamSwitcher';
import { SprintSelector } from './SprintSelector';
import styles from './DashboardTopBar.module.css';

interface DashboardTopBarProps {
  onMenuClick: () => void;
}

export function DashboardTopBar({ onMenuClick }: DashboardTopBarProps) {
  const { dashboard } = useDashboard();
  const [role, setRole] = useState<'manager' | 'general'>('manager');
  const memberDrawer = useEmployeeDrawer();
  const sprint = dashboard?.data.sprint;
  const freshness = dashboard?.data.dataFreshness;

  return <>
    <header className={styles.topBar}>
      <button
        onClick={onMenuClick}
        className={`${styles.menuButton} focus-ring`}
        aria-label="Open menu"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <path d="M3 5h14M3 10h14M3 15h14" />
        </svg>
      </button>

      <TeamSwitcher
        members={dashboard?.members ?? []}
        canSelectMembers={role === 'manager'}
        onSelectMember={memberDrawer.openDrawer}
      />

      <div className={styles.divider} />

      <SprintSelector />

      <span className={styles.sprintPill}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
          <circle cx="6" cy="6" r="4.5" />
          <path d="M6 3.5V6l1.5 1.5" />
        </svg>
        {sprint ? `Day ${sprint.dayNumber} of ${sprint.totalDays}` : 'No sprint selected'}
      </span>

      <div className={styles.spacer} />

      <div className={styles.roleToggle}>
        {(['manager', 'general'] as const).map(option => (
          <button
            key={option}
            onClick={() => setRole(option)}
            className={`${styles.roleButton} ${role === option ? styles.active : ''} focus-ring`}
            aria-pressed={role === option}
          >
            {option}
          </button>
        ))}
      </div>

      <div className={styles.syncStatus}>
        <span className={styles.syncItem}>
          <span className={styles.syncDot} />
          Jira {formatTime(freshness?.jiraLastSyncedAt ?? null)}
        </span>
        <span className={styles.syncItem}>
          <span className={styles.syncDot} />
          PaySpace {formatTime(freshness?.payspaceLastSyncedAt ?? null)}
        </span>
      </div>

      <div className={styles.userProfile}>
        <div className={styles.avatar}>
          BN
        </div>
        <div className={styles.userInfo}>
          <div className={styles.userName}>B. Ndaba</div>
          <div className={styles.userRole}>Eng. Manager</div>
        </div>
      </div>
    </header>
    <EmployeeProfileDrawer
      member={memberDrawer.selectedMember}
      issues={dashboard?.issues ?? []}
      isOpen={memberDrawer.isOpen}
      onClose={memberDrawer.closeDrawer}
    />
  </>;
}
