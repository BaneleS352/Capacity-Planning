'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import type { Team } from '@/types/dashboard';
import type { TeamMember } from '@/types/employee';
import styles from './TeamSwitcher.module.css';

interface TeamSwitcherProps {
  members: TeamMember[];
  canSelectMembers: boolean;
  onSelectMember: (member: TeamMember) => void;
}

export function TeamSwitcher({
  members,
  canSelectMembers,
  onSelectMember,
}: TeamSwitcherProps) {
  const { teams, selectedTeamId, selectTeam: onSelectTeam } = useDashboard();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const selected = teams.find(team => team.id === selectedTeamId) ?? teams[0];

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();

    return teams.filter(team => {
      const teamMatches =
        team.name.toLowerCase().includes(query) ||
        team.department.toLowerCase().includes(query) ||
        team.portfolio?.toLowerCase().includes(query);
      const memberMatches = team.id === selectedTeamId && members.some(member =>
        member.name.toLowerCase().includes(query) || member.role.toLowerCase().includes(query),
      );

      return teamMatches || memberMatches;
    });
  }, [members, search, selectedTeamId, teams]);

  const hierarchy = useMemo(() => {
    const portfolios = new Map<string, Map<string, Team[]>>();

    filtered.forEach(team => {
      const portfolio = team.portfolio || 'Organization';
      const departments = portfolios.get(portfolio) ?? new Map<string, Team[]>();
      const departmentTeams = departments.get(team.department) ?? [];
      departmentTeams.push(team);
      departments.set(team.department, departmentTeams);
      portfolios.set(portfolio, departments);
    });

    return Array.from(portfolios, ([portfolio, departments]) => ({
      portfolio,
      departments: Array.from(departments, ([department, departmentTeams]) => ({
        department,
        teams: departmentTeams.sort((a, b) => a.name.localeCompare(b.name)),
      })).sort((a, b) => a.department.localeCompare(b.department)),
    })).sort((a, b) => a.portfolio.localeCompare(b.portfolio));
  }, [filtered]);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selectTeam = (team: Team) => {
    onSelectTeam(team.id);
    setOpen(false);
    setSearch('');
  };

  const selectMember = (member: TeamMember) => {
    onSelectMember(member);
    setOpen(false);
    setSearch('');
  };

  return (
    <div className={styles.container} ref={ref}>
      <button
        onClick={() => setOpen(current => !current)}
        disabled={teams.length === 0}
        className={`${styles.trigger} focus-ring`}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className={styles.triggerText}>{selected?.name ?? 'No teams'}</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className={`${styles.triggerIcon} ${open ? styles.isOpen : ''}`} aria-hidden="true">
          <path d="M3 4.5L6 7.5L9 4.5" />
        </svg>
      </button>

      {open && (
        <div className={styles.dropdown}>
          <div className={styles.searchContainer}>
            <input
              type="text"
              placeholder="Search teams"
              value={search}
              onChange={event => {
                setSearch(event.target.value);
                setActiveIndex(0);
              }}
              onKeyDown={event => {
                if (event.key === 'ArrowDown') {
                  event.preventDefault();
                  setActiveIndex(current => Math.min(current + 1, filtered.length - 1));
                }

                if (event.key === 'ArrowUp') {
                  event.preventDefault();
                  setActiveIndex(current => Math.max(current - 1, 0));
                }

                if (event.key === 'Enter' && filtered[activeIndex]) {
                  selectTeam(filtered[activeIndex]);
                }

                if (event.key === 'Escape') {
                  setOpen(false);
                }
              }}
              className={styles.searchInput}
              autoFocus
            />
          </div>

          <div className={styles.listContainer} role="listbox" aria-label="Organization teams">
            {hierarchy.map(({ portfolio, departments }) => (
              <div key={portfolio} className={styles.portfolioGroup}>
                <div className={styles.portfolioHeader}>
                  <svg className={styles.treeMark} width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.25" aria-hidden="true">
                    <path d="M2 5.5 6.5 2 11 5.5V11H2V5.5Z" />
                    <path d="M5 11V7.5h3V11" />
                  </svg>
                  {portfolio}
                </div>
                {departments.map(({ department, teams: departmentTeams }) => (
                  <div key={`${portfolio}-${department}`} className={styles.departmentGroup}>
                    <div className={styles.departmentHeader}>{department}</div>
                    {departmentTeams.map(team => {
                      const index = filtered.findIndex(candidate => candidate.id === team.id);
                      const active = selected?.id === team.id;
                      const highlighted = activeIndex === index;
                      const visibleMembers = active && canSelectMembers
                        ? members.filter(member => {
                          const query = search.trim().toLowerCase();
                          return !query || member.name.toLowerCase().includes(query)
                            || member.role.toLowerCase().includes(query)
                            || team.name.toLowerCase().includes(query)
                            || team.department.toLowerCase().includes(query);
                        })
                        : [];

                      return (
                        <div key={team.id} className={styles.teamBranch}>
                          <button
                            onMouseEnter={() => setActiveIndex(index)}
                            onClick={() => selectTeam(team)}
                            className={`${styles.option} ${active ? styles.active : ''} ${highlighted ? styles.highlighted : ''}`}
                            role="option"
                            aria-selected={active}
                          >
                            <span className={styles.branchLine} aria-hidden="true" />
                            {team.isFavourite && (
                              <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true" className={styles.favouriteIcon}>
                                <path d="M6 1.2l1.35 2.9 3.15.39-2.33 2.16.6 3.13L6 8.22 3.23 9.78l.6-3.13L1.5 4.49l3.15-.39L6 1.2z" />
                              </svg>
                            )}
                            <span className={styles.optionText}>{team.name}</span>
                            {active && <span className={styles.selectedLabel}>Selected</span>}
                          </button>

                          {visibleMembers.length > 0 && (
                            <div className={styles.memberList} aria-label={`${team.name} members`}>
                              <div className={styles.memberHeader}>Team members</div>
                              {visibleMembers.map(member => (
                                <button
                                  key={member.id}
                                  onClick={() => selectMember(member)}
                                  className={styles.memberOption}
                                  role="option"
                                  aria-selected="false"
                                >
                                  <span className={styles.memberAvatar}>{member.avatarInitials}</span>
                                  <span className={styles.memberText}>
                                    <span className={styles.memberName}>{member.name}</span>
                                    <span className={styles.memberRole}>{member.role}</span>
                                  </span>
                                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                                    <path d="m4.5 2.5 3.5 3.5-3.5 3.5" />
                                  </svg>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            ))}
            {hierarchy.length === 0 && (
              <div className={styles.emptyState}>No teams or members match your search.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
