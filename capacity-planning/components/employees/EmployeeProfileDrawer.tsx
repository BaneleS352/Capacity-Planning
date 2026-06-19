'use client';

import { useEffect, useMemo, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Drawer } from '@/components/ui/Drawer';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { getEmployeeProfile } from '@/lib/api/client';
import type {
  ApiEmployeeProfile,
  ApiEmployeeStoryPointsHistory,
  ApiJiraIssue,
} from '@/lib/api/types';
import { formatHours, formatStoryPoints } from '@/lib/formatters';
import { getLeaveLabel } from '@/lib/statusUtils';
import type { TeamMember } from '@/types/employee';
import type { JiraIssue } from '@/types/jira';
import styles from './EmployeeProfileDrawer.module.css';

interface EmployeeProfileDrawerProps {
  member: TeamMember | null;
  issues: JiraIssue[];
  isOpen: boolean;
  onClose: () => void;
}

interface DisplayIssue {
  id: string;
  key: string;
  title: string;
  storyPoints: number;
  blocked: boolean;
  carryOver: boolean;
  completedAt: string | null;
}

export function EmployeeProfileDrawer({
  member,
  issues,
  isOpen,
  onClose,
}: EmployeeProfileDrawerProps) {
  const [loadedProfile, setLoadedProfile] = useState<ApiEmployeeProfile | null>(null);
  const [requestError, setRequestError] = useState<{ memberId: string; message: string } | null>(null);
  const profile = loadedProfile?.employee.id === member?.id ? loadedProfile : null;
  const error = requestError && requestError.memberId === member?.id
    ? requestError.message
    : null;
  const loading = Boolean(isOpen && member && !profile && !error);

  useEffect(() => {
    if (!isOpen || !member) return;

    const controller = new AbortController();
    getEmployeeProfile(member.id, controller.signal)
      .then(response => {
        setLoadedProfile(response);
        setRequestError(null);
      })
      .catch(requestError => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
        setRequestError({
          memberId: member.id,
          message: requestError instanceof Error
            ? requestError.message
            : 'Unable to load employee profile.',
        });
      });

    return () => controller.abort();
  }, [isOpen, member]);

  const fallbackIssues = useMemo(
    () => member
      ? issues.filter(issue => issue.assigneeId === member.id).map(mapDashboardIssue)
      : [],
    [issues, member],
  );
  const currentIssues = profile?.current_issues.map(mapApiIssue) ?? fallbackIssues;
  const completedIssues = profile?.completed_issues.map(mapApiIssue) ?? [];
  const blockedIssues = currentIssues.filter(issue => issue.blocked);
  const carryOverIssues = currentIssues.filter(issue => issue.carryOver);
  const assignedPoints = profile?.current_capacity
    ? numberValue(profile.current_capacity.assigned_story_points)
    : currentIssues.reduce((total, issue) => total + issue.storyPoints, 0);
  const currentHistory = profile?.story_points_history[0];

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={member ? member.name : 'Employee'}
      width="xl"
    >
      {member && (
        <div className={styles.content}>
          <section className={styles.headerSection}>
            <div className={styles.avatar}>{member.avatarInitials}</div>
            <div className={styles.info}>
              <div className={styles.nameGroup}>
                <h3 className={styles.name}>{member.name}</h3>
                <Badge variant={member.riskLevel}>{member.riskLevel}</Badge>
              </div>
              <p className={styles.role}>{member.role}</p>
              <p className={styles.meta}>
                {profile?.employee.department || 'Engineering'}
                {profile?.employee.location_code ? ` / ${profile.employee.location_code}` : ''}
              </p>
            </div>
          </section>

          {loading && <div className={styles.loadingState}>Loading employee history...</div>}
          {error && <div className={styles.errorState}>{error}</div>}

          <section className={styles.metricsGrid}>
            <ProfileMetric label="Sprint capacity" value={formatHours(member.sprintCapacityHours)} />
            <ProfileMetric label="Assigned story points" value={formatStoryPoints(assignedPoints)} />
            <ProfileMetric
              label="Completed story points"
              value={formatStoryPoints(numberValue(currentHistory?.completed_story_points))}
            />
            <ProfileMetric label="Completed work items" value={String(completedIssues.length)} />
          </section>

          {profile && (
            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <div>
                  <h4 className={styles.sectionTitle}>Story Points Over Time</h4>
                  <p className={styles.sectionSubtitle}>Assigned and completed work by sprint</p>
                </div>
                <div className={styles.legend} aria-label="Chart legend">
                  <span><i className={styles.assignedSwatch} />Assigned</span>
                  <span><i className={styles.completedSwatch} />Completed</span>
                </div>
              </div>
              <StoryPointsLineChart history={profile.story_points_history} />
            </section>
          )}

          {profile && (
            <section className={styles.section}>
              <h4 className={styles.sectionTitle}>Employee Details</h4>
              <div className={styles.detailsGrid}>
                <Detail label="Email" value={profile.employee.corporate_email} />
                <Detail label="Employment" value={titleCase(profile.employee.employment_type)} />
                <Detail label="Location" value={profile.employee.location_code || 'Not specified'} />
                <Detail label="FTE" value={`${numberValue(profile.employee.fte_factor) * 100}%`} />
                <Detail
                  label="Team allocation"
                  value={`${numberValue(profile.memberships[0]?.allocation_percent)}%`}
                />
                <Detail
                  label="Source links"
                  value={`${profile.employee.jira_account_id ? 'Jira' : 'No Jira'} / ${profile.employee.payspace_employee_number ? 'PaySpace' : 'No PaySpace'}`}
                />
              </div>
            </section>
          )}

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h4 className={styles.sectionTitle}>Current Load</h4>
              <span className={styles.loadPercent}>{member.utilisationPercent}%</span>
            </div>
            <ProgressBar value={member.utilisationPercent} colour={member.riskLevel} />
            {member.riskReason && <p className={styles.riskReason}>{member.riskReason}</p>}
          </section>

          <IssueSection title="Current Jira Work" issues={currentIssues} empty="No assigned sprint issues." />
          <IssueSection title="Completed Work" issues={completedIssues} empty="No completed Jira work recorded." />

          <section className={styles.metricsGrid}>
            <ProfileMetric label="Blocked work" value={String(blockedIssues.length)} />
            <ProfileMetric label="Carry-over" value={String(carryOverIssues.length)} />
          </section>

          <section className={styles.section}>
            <h4 className={styles.sectionTitle}>Availability and Leave</h4>
            <div className={styles.availabilityBox}>
              <div className={styles.leaveInfo}>
                <span className={styles.leaveLabel}>{getLeaveLabel(member.leaveType, true)}</span>
                <span className={styles.leaveDays}>{member.leaveDays} days this sprint</span>
              </div>
              {profile?.leave.map(leave => (
                <div key={leave.id} className={styles.leaveRecord}>
                  <span>{titleCase(leave.leave_type)}</span>
                  <span>{formatDate(leave.start_date)} - {formatDate(leave.end_date)}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </Drawer>
  );
}

function StoryPointsLineChart({ history }: { history: ApiEmployeeStoryPointsHistory[] }) {
  const points = [...history].reverse();
  if (points.length === 0) {
    return <div className={styles.chartEmpty}>No sprint history is available for this employee.</div>;
  }

  const width = 560;
  const height = 220;
  const left = 38;
  const right = 16;
  const top = 18;
  const bottom = 42;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const maxValue = Math.max(
    5,
    ...points.flatMap(point => [
      numberValue(point.assigned_story_points),
      numberValue(point.completed_story_points),
    ]),
  );
  const x = (index: number) => left + (points.length === 1 ? plotWidth / 2 : index * plotWidth / (points.length - 1));
  const y = (value: number) => top + plotHeight - value / maxValue * plotHeight;
  const assignedPath = points.map((point, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(numberValue(point.assigned_story_points))}`).join(' ');
  const completedPath = points.map((point, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(numberValue(point.completed_story_points))}`).join(' ');

  return (
    <div className={styles.chartContainer}>
      <svg className={styles.chart} viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="story-points-chart-title story-points-chart-description">
        <title id="story-points-chart-title">Story points by sprint</title>
        <desc id="story-points-chart-description">Line chart comparing assigned and completed story points over time.</desc>
        {[0, 0.25, 0.5, 0.75, 1].map(step => {
          const value = Math.round(maxValue * step);
          const gridY = y(value);
          return <g key={step}>
            <line x1={left} x2={width - right} y1={gridY} y2={gridY} className={styles.gridLine} />
            <text x={left - 8} y={gridY + 3} textAnchor="end" className={styles.axisLabel}>{value}</text>
          </g>;
        })}
        <path d={assignedPath} className={styles.assignedLine} />
        <path d={completedPath} className={styles.completedLine} />
        {points.map((point, index) => (
          <g key={point.sprint_id}>
            <circle cx={x(index)} cy={y(numberValue(point.assigned_story_points))} r="3.5" className={styles.assignedPoint}>
              <title>{point.sprint_name}: {point.assigned_story_points} assigned</title>
            </circle>
            <circle cx={x(index)} cy={y(numberValue(point.completed_story_points))} r="3.5" className={styles.completedPoint}>
              <title>{point.sprint_name}: {point.completed_story_points} completed</title>
            </circle>
            <text x={x(index)} y={height - 18} textAnchor="middle" className={styles.axisLabel}>
              {formatShortDate(point.end_at)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function IssueSection({ title, issues, empty }: { title: string; issues: DisplayIssue[]; empty: string }) {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <h4 className={styles.sectionTitle}>{title}</h4>
        <span className={styles.itemCount}>{issues.length}</span>
      </div>
      <div className={styles.issueList}>
        {issues.map(issue => (
          <div key={issue.id} className={styles.issueItem}>
            <div className={styles.issueItemContent}>
              <div className={styles.issueInfo}>
                <div className={styles.issueKeyGroup}>
                  <span className={styles.issueKey}>{issue.key}</span>
                  {issue.blocked && <Badge variant="red">Blocked</Badge>}
                  {issue.carryOver && <Badge variant="amber">Carry-over</Badge>}
                  {issue.completedAt && <Badge variant="green">Done</Badge>}
                </div>
                <p className={styles.issueTitle}>{issue.title}</p>
              </div>
              <span className={styles.issuePoints}>{formatStoryPoints(issue.storyPoints)}</span>
            </div>
          </div>
        ))}
        {issues.length === 0 && <div className={styles.emptyIssues}>{empty}</div>}
      </div>
    </section>
  );
}

function ProfileMetric({ label, value }: { label: string; value: string }) {
  return <div className={styles.metricCard}>
    <div className={styles.metricLabel}>{label}</div>
    <div className={styles.metricValue}>{value}</div>
  </div>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className={styles.detailItem}>
    <span className={styles.detailLabel}>{label}</span>
    <span className={styles.detailValue}>{value}</span>
  </div>;
}

function mapApiIssue(issue: ApiJiraIssue): DisplayIssue {
  return {
    id: issue.id,
    key: issue.issue_key,
    title: issue.summary,
    storyPoints: numberValue(issue.story_points),
    blocked: issue.blocked,
    carryOver: Boolean(issue.normalized_fields.carry_over),
    completedAt: issue.completed_at,
  };
}

function mapDashboardIssue(issue: JiraIssue): DisplayIssue {
  return {
    id: issue.id,
    key: issue.key,
    title: issue.title,
    storyPoints: issue.storyPoints,
    blocked: issue.blocked,
    carryOver: issue.carryOver,
    completedAt: issue.status === 'Done' ? new Date().toISOString() : null,
  };
}

function numberValue(value: string | number | null | undefined): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function titleCase(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, character => character.toUpperCase());
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' })
    .format(new Date(`${value}T12:00:00Z`));
}

function formatShortDate(value: string): string {
  return new Intl.DateTimeFormat('en-ZA', { month: 'short', day: 'numeric' })
    .format(new Date(value));
}
