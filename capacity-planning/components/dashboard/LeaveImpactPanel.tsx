'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { getLeaveLabel } from '@/lib/statusUtils';
import type { TeamMember } from '@/types/employee';
import styles from './LeaveImpactPanel.module.css';

interface LeaveImpactPanelProps {
  members: TeamMember[];
}

export function LeaveImpactPanel({ members }: LeaveImpactPanelProps) {
  const [managerView, setManagerView] = useState(false);
  const impactedMembers = members.filter(member => member.leaveDays > 0);
  const totalLeaveDays = impactedMembers.reduce((total, member) => total + member.leaveDays, 0);
  const affectedRoles = Array.from(new Set(impactedMembers.map(member => member.role)));

  return (
    <Card>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Leave Impact</h2>
            <p className={styles.subtitle}>
              {totalLeaveDays} person-days removed from sprint capacity
            </p>
          </div>
          <div className={styles.toggleContainer}>
            <button
              onClick={() => setManagerView(false)}
              className={`${styles.toggleButton} focus-ring ${!managerView ? styles.active : ''}`}
              aria-pressed={!managerView}
            >
              General
            </button>
            <button
              onClick={() => setManagerView(true)}
              className={`${styles.toggleButton} focus-ring ${managerView ? styles.active : ''}`}
              aria-pressed={managerView}
            >
              Manager
            </button>
          </div>
        </div>

        <div className={styles.metricsGrid}>
          <ImpactMetric label="People impacted" value={String(impactedMembers.length)} />
          <ImpactMetric label="Roles impacted" value={String(affectedRoles.length)} />
        </div>

        <div className={styles.memberList}>
          {impactedMembers.map(member => (
            <div key={member.id} className={styles.memberItem}>
              <div className={styles.memberInfo}>
                <div className={styles.memberName}>{member.name}</div>
                <div className={styles.memberRole}>{member.role}</div>
              </div>
              <div className={styles.memberStats}>
                <Badge variant={member.riskLevel}>{getLeaveLabel(member.leaveType, managerView)}</Badge>
                <span className={styles.leaveDays}>{member.leaveDays}d</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function ImpactMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValue}>{value}</div>
    </div>
  );
}
