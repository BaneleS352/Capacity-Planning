'use client';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { utilisationToColour } from '@/lib/statusUtils';
import { formatStoryPoints } from '@/lib/formatters';
import type { TeamMember } from '@/types/employee';
import styles from './WorkloadDistributionChart.module.css';

interface WorkloadDistributionChartProps {
  members: TeamMember[];
}

export function WorkloadDistributionChart({ members }: WorkloadDistributionChartProps) {
  const sortedMembers = [...members].sort((a, b) => b.utilisationPercent - a.utilisationPercent);
  const overCapacityCount = members.filter(member => member.utilisationPercent > 100).length;

  return (
    <Card>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Workload Distribution</h2>
            <p className={styles.subtitle}>Assigned story points by person</p>
          </div>
          <Badge variant={overCapacityCount > 0 ? 'red' : 'green'}>
            {overCapacityCount} over
          </Badge>
        </div>

        <div className={styles.list}>
          {sortedMembers.map(member => {
            const colour = utilisationToColour(member.utilisationPercent);
            const width = Math.min(member.utilisationPercent, 130);

            const barClass = {
              green: styles.barGreen,
              amber: styles.barAmber,
              red: styles.barRed,
              blue: styles.barBlue,
              grey: styles.barGrey,
            }[colour];

            return (
              <div key={member.id} className={styles.item}>
                <div className={styles.info}>
                  <div className={styles.nameGroup}>
                    <span className={styles.name}>{member.name}</span>
                    <span className={styles.points}>{formatStoryPoints(member.assignedStoryPoints)}</span>
                  </div>
                  <span className={styles.percent}>
                    {member.utilisationPercent}%
                  </span>
                </div>
                <div className={styles.track}>
                  <div
                    className={`${styles.bar} ${barClass}`}
                    style={{ width: `${width / 1.3}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
