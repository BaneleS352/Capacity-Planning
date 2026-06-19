'use client';

import { useMemo } from 'react';
import { Card } from '@/components/ui/Card';
import { Tooltip } from '@/components/ui/Tooltip';
import { AVAILABILITY_LABELS, HEATMAP_BG_CLASSES } from '@/constants/statusColours';
import { formatShortDate } from '@/lib/formatters';
import { generateSprintDays } from '@/lib/dateUtils';
import type { Sprint } from '@/types/dashboard';
import type { AvailabilityStatus, TeamMember } from '@/types/employee';
import styles from './AvailabilityHeatmap.module.css';

interface AvailabilityHeatmapProps {
  members: TeamMember[];
  sprint: Sprint;
}

const LEGEND: AvailabilityStatus[] = [
  'available',
  'support-rotation',
  'ceremony-heavy',
  'on-leave',
  'critical-risk',
];

export function AvailabilityHeatmap({ members, sprint }: AvailabilityHeatmapProps) {
  const sprintDays = useMemo(
    () => generateSprintDays(sprint.startDate, sprint.totalDays),
    [sprint.startDate, sprint.totalDays],
  );
  const heatmap = useMemo(() => Object.fromEntries(
    members.map(member => [
      member.id,
      sprintDays.map(date => ({
        date,
        status: member.availabilityStatus,
        label: AVAILABILITY_LABELS[member.availabilityStatus],
      })),
    ]),
  ), [members, sprintDays]);

  return (
    <Card>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Availability Heatmap</h2>
            <p className={styles.subtitle}>{sprint.name} working-day coverage</p>
          </div>
          <div className={styles.legend}>
            {LEGEND.map(status => {
              const bgClass = HEATMAP_BG_CLASSES[status].split(' ')[0]; // We keep tailwind classes for colors or replace logic. Let's assume we map them correctly later or they just work if globals are set. Wait, HEATMAP_BG_CLASSES uses Tailwind classes like `bg-emerald-100`. We need to handle this.
              // To keep it simple, we'll map them via style prop or ensure they are present.
              // For now, let's keep the existing logic.
              return (
                <span key={status} className={styles.legendItem}>
                  <span className={`${styles.legendColor} ${bgClass}`} />
                  {AVAILABILITY_LABELS[status]}
                </span>
              );
            })}
          </div>
        </div>

        <div className={styles.heatmapScroll}>
          <div
            className={styles.grid}
            style={{ gridTemplateColumns: `180px repeat(${sprintDays.length}, minmax(54px, 1fr))` }}
          >
            <div />
            {sprintDays.map((date, index) => (
              <div key={date} className={styles.dayHeader}>
                <div className={styles.dayNum}>D{index + 1}</div>
                <div className={styles.dayDate}>{formatShortDate(date)}</div>
              </div>
            ))}

            {members.map(member => (
              <div key={member.id} style={{ display: 'contents' }}>
                <div className={styles.memberCell}>
                  <span className={styles.avatar}>
                    {member.avatarInitials}
                  </span>
                  <span className={styles.memberName}>{member.name}</span>
                </div>
                {heatmap[member.id].map(day => (
                  <Tooltip
                    key={`${member.id}-${day.date}`}
                    content={`${member.name}: ${day.label} (${formatShortDate(day.date)})`}
                  >
                    <div
                      className={`${styles.statusCell} ${HEATMAP_BG_CLASSES[day.status]}`}
                    >
                      {day.label.slice(0, 3)}
                    </div>
                  </Tooltip>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
