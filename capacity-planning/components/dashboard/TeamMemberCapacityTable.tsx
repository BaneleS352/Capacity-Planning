'use client';

import { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmployeeProfileDrawer } from '@/components/employees/EmployeeProfileDrawer';
import { useEmployeeDrawer } from '@/hooks/useEmployeeDrawer';
import { availabilityToColour, getLeaveLabel } from '@/lib/statusUtils';
import { formatHours, formatStoryPoints } from '@/lib/formatters';
import type { TeamMember, AvailabilityStatus } from '@/types/employee';
import type { JiraIssue } from '@/types/jira';
import styles from './TeamMemberCapacityTable.module.css';

type SortKey = 'name' | 'role' | 'assignedStoryPoints' | 'utilisationPercent' | 'riskLevel';
type SortDirection = 'asc' | 'desc';

interface TeamMemberCapacityTableProps {
  members: TeamMember[];
  issues: JiraIssue[];
}

const RISK_ORDER = {
  red: 0,
  amber: 1,
  green: 2,
} as const;

export function TeamMemberCapacityTable({ members, issues }: TeamMemberCapacityTableProps) {
  const [query, setQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<'all' | TeamMember['riskLevel']>('all');
  const [availabilityFilter, setAvailabilityFilter] = useState<'all' | AvailabilityStatus>('all');
  const [sortKey, setSortKey] = useState<SortKey>('utilisationPercent');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const drawer = useEmployeeDrawer();

  const availabilityOptions = useMemo(
    () => Array.from(new Set(members.map(member => member.availabilityStatus))),
    [members],
  );

  const visibleMembers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return members
      .filter(member => {
        const matchesQuery =
          member.name.toLowerCase().includes(normalizedQuery) ||
          member.role.toLowerCase().includes(normalizedQuery);
        const matchesRisk = riskFilter === 'all' || member.riskLevel === riskFilter;
        const matchesAvailability =
          availabilityFilter === 'all' || member.availabilityStatus === availabilityFilter;

        return matchesQuery && matchesRisk && matchesAvailability;
      })
      .sort((a, b) => {
        const modifier = sortDirection === 'asc' ? 1 : -1;

        if (sortKey === 'riskLevel') {
          return (RISK_ORDER[a.riskLevel] - RISK_ORDER[b.riskLevel]) * modifier;
        }

        const aValue = a[sortKey];
        const bValue = b[sortKey];

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return (aValue - bValue) * modifier;
        }

        return String(aValue).localeCompare(String(bValue)) * modifier;
      });
  }, [availabilityFilter, members, query, riskFilter, sortDirection, sortKey]);

  const setSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(current => current === 'asc' ? 'desc' : 'asc');
      return;
    }

    setSortKey(key);
    setSortDirection(key === 'name' || key === 'role' ? 'asc' : 'desc');
  };

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Team Capacity</h2>
          <p className={styles.subtitle}>{visibleMembers.length} people in sprint scope</p>
        </div>

        <div className={styles.filters}>
          <input
            type="search"
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="Search people"
            className={styles.input}
          />
          <select
            value={riskFilter}
            onChange={event => setRiskFilter(event.target.value as typeof riskFilter)}
            className={styles.select}
          >
            <option value="all">All risks</option>
            <option value="red">Red</option>
            <option value="amber">Amber</option>
            <option value="green">Green</option>
          </select>
          <select
            value={availabilityFilter}
            onChange={event => setAvailabilityFilter(event.target.value as typeof availabilityFilter)}
            className={styles.select}
          >
            <option value="all">All availability</option>
            {availabilityOptions.map(option => (
              <option key={option} value={option}>{option.replace(/-/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead className={styles.thead}>
            <tr>
              <SortableHeader label="Employee" active={sortKey === 'name'} direction={sortDirection} onClick={() => setSort('name')} />
              <SortableHeader label="Role" active={sortKey === 'role'} direction={sortDirection} onClick={() => setSort('role')} />
              <th className={styles.th}>Availability</th>
              <th className={styles.th}>Leave</th>
              <th className={styles.th}>Daily</th>
              <th className={styles.th}>Sprint</th>
              <SortableHeader label="Assigned" active={sortKey === 'assignedStoryPoints'} direction={sortDirection} onClick={() => setSort('assignedStoryPoints')} />
              <SortableHeader label="Utilisation" active={sortKey === 'utilisationPercent'} direction={sortDirection} onClick={() => setSort('utilisationPercent')} />
              <SortableHeader label="Risk" active={sortKey === 'riskLevel'} direction={sortDirection} onClick={() => setSort('riskLevel')} />
            </tr>
          </thead>
          <tbody className={styles.tbody}>
            {visibleMembers.map(member => {
              const memberIssues = issues.filter(issue => issue.assigneeId === member.id);
              const availabilityColour = availabilityToColour(member.availabilityStatus);

              return (
                <tr
                  key={member.id}
                  tabIndex={0}
                  onClick={() => drawer.openDrawer(member)}
                  onKeyDown={event => {
                    if (event.key === 'Enter') drawer.openDrawer(member);
                  }}
                  className={styles.tr}
                >
                  <td className={styles.td}>
                    <div className={styles.memberCell}>
                      <div className={styles.avatar}>
                        {member.avatarInitials}
                      </div>
                      <div>
                        <div className={styles.memberName}>{member.name}</div>
                        <div className={styles.issueCount}>{memberIssues.length} issues</div>
                      </div>
                    </div>
                  </td>
                  <td className={styles.td}>{member.role}</td>
                  <td className={styles.td}>
                    <Badge variant={availabilityColour}>{member.availabilityStatus.replace(/-/g, ' ')}</Badge>
                  </td>
                  <td className={styles.td}>
                    {getLeaveLabel(member.leaveType, false)}
                  </td>
                  <td className={styles.td}>{formatHours(member.dailyCapacityHours)}</td>
                  <td className={styles.td}>{formatHours(member.sprintCapacityHours)}</td>
                  <td className={`${styles.td} ${styles.boldText}`}>
                    {formatStoryPoints(member.assignedStoryPoints)}
                  </td>
                  <td className={styles.td}>
                    <div style={{ width: '8rem' }}>
                      <ProgressBar
                        value={member.utilisationPercent}
                        colour={member.riskLevel}
                        showPercent
                      />
                    </div>
                  </td>
                  <td className={styles.td}>
                    <Badge variant={member.riskLevel}>{member.riskLevel}</Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <EmployeeProfileDrawer
        member={drawer.selectedMember}
        issues={issues}
        isOpen={drawer.isOpen}
        onClose={drawer.closeDrawer}
      />
    </section>
  );
}

function SortableHeader({
  label,
  active,
  direction,
  onClick,
}: {
  label: string;
  active: boolean;
  direction: SortDirection;
  onClick: () => void;
}) {
  return (
    <th className={styles.th}>
      <button
        onClick={onClick}
        className={`${styles.sortButton} focus-ring`}
        style={{ opacity: active ? 1 : 0.5 }}
      >
        {label}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className={`${styles.sortIcon} ${active && direction === 'asc' ? styles.asc : ''}`} aria-hidden="true">
          <path d="M2.5 4 5 6.5 7.5 4" />
        </svg>
      </button>
    </th>
  );
}
