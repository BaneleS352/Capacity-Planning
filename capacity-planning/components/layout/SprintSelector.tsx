'use client';

import { useEffect, useRef, useState } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { formatShortDate } from '@/lib/formatters';
import styles from './SprintSelector.module.css';

export function SprintSelector() {
  const { sprints, selectedSprintId, selectSprint } = useDashboard();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = sprints.find(sprint => sprint.id === selectedSprintId) ?? sprints[0];

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className={styles.container} ref={ref}>
      <button
        onClick={() => setOpen(current => !current)}
        disabled={sprints.length === 0}
        className={`${styles.trigger} focus-ring`}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        {selected?.name ?? 'No sprints'}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className={`${styles.triggerIcon} ${open ? styles.isOpen : ''}`} aria-hidden="true">
          <path d="M2.5 3.75L5 6.25L7.5 3.75" />
        </svg>
      </button>

      {open && (
        <div className={styles.dropdown} role="listbox">
          {sprints.map(sprint => (
            <button
              key={sprint.id}
              onClick={() => {
                selectSprint(sprint.id);
                setOpen(false);
              }}
              className={`${styles.option} ${selected?.id === sprint.id ? styles.active : ''}`}
              role="option"
              aria-selected={selected?.id === sprint.id}
            >
              <span className={styles.optionLabel}>{sprint.name}</span>
              <span className={styles.optionDate}>
                {formatShortDate(sprint.startDate)} - {formatShortDate(sprint.endDate)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
