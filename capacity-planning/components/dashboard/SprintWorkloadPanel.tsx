'use client';

import { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { STALE_IN_PROGRESS_DAYS } from '@/constants/capacityThresholds';
import { formatStoryPoints } from '@/lib/formatters';
import type { StatusColour } from '@/constants/statusColours';
import type { TeamMember } from '@/types/employee';
import type { IssuePriority, IssueStatus, IssueType, JiraIssue } from '@/types/jira';
import styles from './SprintWorkloadPanel.module.css';

interface SprintWorkloadPanelProps {
  issues: JiraIssue[];
  members: TeamMember[];
}

type FlagFilter = 'all' | 'blocked' | 'carry-over' | 'added' | 'unassigned' | 'stale';

const STATUS_COLOURS: Record<IssueStatus, StatusColour> = {
  'To Do': 'grey',
  'In Progress': 'blue',
  'In Review': 'amber',
  QA: 'amber',
  Done: 'green',
  Blocked: 'red',
};

const PRIORITY_COLOURS: Record<IssuePriority, StatusColour> = {
  Critical: 'red',
  High: 'amber',
  Medium: 'blue',
  Low: 'grey',
};

export function SprintWorkloadPanel({ issues, members }: SprintWorkloadPanelProps) {
  const [query, setQuery] = useState('');
  const [assigneeId, setAssigneeId] = useState('all');
  const [status, setStatus] = useState<'all' | IssueStatus>('all');
  const [priority, setPriority] = useState<'all' | IssuePriority>('all');
  const [issueType, setIssueType] = useState<'all' | IssueType>('all');
  const [flag, setFlag] = useState<FlagFilter>('all');

  const statuses = useMemo(() => Array.from(new Set(issues.map(issue => issue.status))), [issues]);
  const priorities = useMemo(() => Array.from(new Set(issues.map(issue => issue.priority))), [issues]);
  const issueTypes = useMemo(() => Array.from(new Set(issues.map(issue => issue.issueType))), [issues]);

  const filteredIssues = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return issues.filter(issue => {
      const matchesQuery =
        issue.key.toLowerCase().includes(normalizedQuery) ||
        issue.title.toLowerCase().includes(normalizedQuery) ||
        issue.epic.toLowerCase().includes(normalizedQuery);
      const matchesAssignee = assigneeId === 'all' || issue.assigneeId === assigneeId;
      const matchesStatus = status === 'all' || issue.status === status;
      const matchesPriority = priority === 'all' || issue.priority === priority;
      const matchesType = issueType === 'all' || issue.issueType === issueType;
      const stale = issue.status === 'In Progress' && issue.daysInStatus >= STALE_IN_PROGRESS_DAYS;
      const matchesFlag =
        flag === 'all' ||
        (flag === 'blocked' && issue.blocked) ||
        (flag === 'carry-over' && issue.carryOver) ||
        (flag === 'added' && issue.addedAfterSprintStart) ||
        (flag === 'unassigned' && !issue.assigneeId) ||
        (flag === 'stale' && stale);

      return matchesQuery && matchesAssignee && matchesStatus && matchesPriority && matchesType && matchesFlag;
    });
  }, [assigneeId, flag, issueType, issues, priority, query, status]);

  const totalPoints = filteredIssues.reduce((total, issue) => total + issue.storyPoints, 0);

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div>
            <h2 className={styles.title}>Sprint Workload</h2>
            <p className={styles.subtitle}>
              {filteredIssues.length} issues / {formatStoryPoints(totalPoints)}
            </p>
          </div>
          <input
            type="search"
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="Search Jira work"
            className={styles.searchInput}
          />
        </div>

        <div className={styles.filters}>
          <FilterSelect value={assigneeId} onChange={setAssigneeId}>
            <option value="all">All assignees</option>
            {members.map(member => (
              <option key={member.id} value={member.id}>{member.name}</option>
            ))}
          </FilterSelect>
          <FilterSelect value={status} onChange={value => setStatus(value as typeof status)}>
            <option value="all">All statuses</option>
            {statuses.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </FilterSelect>
          <FilterSelect value={priority} onChange={value => setPriority(value as typeof priority)}>
            <option value="all">All priorities</option>
            {priorities.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </FilterSelect>
          <FilterSelect value={issueType} onChange={value => setIssueType(value as typeof issueType)}>
            <option value="all">All types</option>
            {issueTypes.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </FilterSelect>
          <FilterSelect value={flag} onChange={value => setFlag(value as FlagFilter)}>
            <option value="all">All flags</option>
            <option value="blocked">Blocked</option>
            <option value="carry-over">Carry-over</option>
            <option value="added">Added after start</option>
            <option value="unassigned">Unassigned</option>
            <option value="stale">Stale in progress</option>
          </FilterSelect>
        </div>
      </div>

      <div className={styles.list}>
        {filteredIssues.map(issue => {
          const stale = issue.status === 'In Progress' && issue.daysInStatus >= STALE_IN_PROGRESS_DAYS;

          return (
            <article key={issue.id} className={styles.article}>
              <div className={styles.articleContent}>
                <div className={styles.info}>
                  <div className={styles.tags}>
                    <span className={styles.issueKey}>{issue.key}</span>
                    <Badge variant={STATUS_COLOURS[issue.status]}>{issue.status}</Badge>
                    <Badge variant={PRIORITY_COLOURS[issue.priority]}>{issue.priority}</Badge>
                    <span className={styles.issueType}>{issue.issueType}</span>
                  </div>
                  <h3 className={styles.issueTitle}>{issue.title}</h3>
                  <p className={styles.issueMeta}>
                    {issue.assignee ?? 'Unassigned'} / {issue.epic} / {issue.daysInStatus} days in status
                  </p>
                  {issue.blockedReason && (
                    <p className={styles.blockedReason}>
                      {issue.blockedReason}
                    </p>
                  )}
                </div>
                <div className={styles.pointsContainer}>
                  <span className={styles.storyPoints}>
                    {formatStoryPoints(issue.storyPoints)}
                  </span>
                  {issue.addedAfterSprintStart && <Badge variant="blue">Added</Badge>}
                  {issue.carryOver && <Badge variant="amber">Carry-over</Badge>}
                  {issue.blocked && <Badge variant="red">Blocked</Badge>}
                  {stale && <Badge variant="amber">Stale</Badge>}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function FilterSelect({
  value,
  onChange,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return (
    <select
      value={value}
      onChange={event => onChange(event.target.value)}
      className={styles.select}
    >
      {children}
    </select>
  );
}
