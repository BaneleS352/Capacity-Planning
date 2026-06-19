'use client';

import type { Team, Sprint } from '@/types/dashboard';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { StatusDot } from '@/components/ui/StatusDot';
import { healthToColour } from '@/lib/statusUtils';
import { formatShortDate } from '@/lib/formatters';
import { HEALTH_LABELS } from '@/constants/statusColours';
import styles from './SprintHealthHero.module.css';

interface SprintHealthHeroProps {
  team: Team;
  sprint: Sprint;
}

export function SprintHealthHero({ team, sprint }: SprintHealthHeroProps) {
  const colour = healthToColour(sprint.healthStatus);
  const healthLabel = HEALTH_LABELS[sprint.healthStatus] || 'Unknown';
  const progress = (sprint.dayNumber / sprint.totalDays) * 100;

  const reasonClass = {
    red: styles.reasonRed,
    amber: styles.reasonAmber,
    green: styles.reasonGreen,
    blue: '', // Assuming blue isn't used for health status
    grey: '',
  }[colour];

  return (
    <Card padding="lg">
      <div className={styles.container}>
        {/* Top row: team name, sprint badge, health status */}
        <div className={styles.topRow}>
          <div className={styles.teamInfo}>
            <h1 className={styles.teamName}>{team.name}</h1>
            <div className={styles.sprintMeta}>
              <Badge variant="grey" size="sm">{sprint.name}</Badge>
              <span>{formatShortDate(sprint.startDate)} — {formatShortDate(sprint.endDate)}</span>
            </div>
          </div>

          <div className={styles.statusContainer}>
            <Badge variant={colour} size="md">
              <StatusDot colour={colour} pulse={sprint.healthStatus === 'red'} />
              <span className={styles.statusLabel}>{healthLabel}</span>
            </Badge>
            <div className={styles.dayInfo}>
              Day {sprint.dayNumber} of {sprint.totalDays}
            </div>
          </div>
        </div>

        {/* Sprint progress bar */}
        <div className={styles.progressContainer}>
          <div className={styles.progressTrack}>
            <div
              className={styles.progressBar}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Health reason — prominent */}
        {sprint.healthReason && (
          <div className={`${styles.healthReason} ${reasonClass}`}>
            {sprint.healthReason}
          </div>
        )}

        {/* Team leads */}
        <div className={styles.teamLeads}>
          <span><span className={styles.leadRole}>EM</span> {team.engineeringManager}</span>
          <span><span className={styles.leadRole}>SM</span> {team.scrumMaster}</span>
          <span><span className={styles.leadRole}>PO</span> {team.productOwner}</span>
        </div>
      </div>
    </Card>
  );
}
