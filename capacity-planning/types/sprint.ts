/** Sprint-specific types */

export interface BurndownPoint {
  day: number;
  date: string;
  ideal: number;
  actual: number | null;
  label: string;
}

export interface ScopeChange {
  id: string;
  date: string;
  type: 'added' | 'removed' | 're-estimated';
  issueKey: string;
  issueTitle: string;
  storyPoints: number;
  reason: string;
  dayNumber: number;
}

export interface SprintDay {
  dayNumber: number;
  date: string;
  isWeekend: boolean;
  isToday: boolean;
  label: string;
}

export interface PlannedVsActual {
  category: string;
  planned: number;
  actual: number;
}
