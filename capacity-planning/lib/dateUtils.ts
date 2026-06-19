/** Date and sprint day calculation utilities */

/** Calculate which day of the sprint today is (1-indexed) */
export function calculateSprintDay(startDate: string, endDate: string): { dayNumber: number; totalDays: number } {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();

  const totalDays = countBusinessDays(start, end);
  const elapsed = countBusinessDays(start, today);

  return {
    dayNumber: Math.min(Math.max(elapsed, 1), totalDays),
    totalDays,
  };
}

/** Count business days (Mon–Fri) between two dates, inclusive */
export function countBusinessDays(start: Date, end: Date): number {
  let count = 0;
  const current = new Date(start);

  while (current <= end) {
    const dayOfWeek = current.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      count++;
    }
    current.setDate(current.getDate() + 1);
  }

  return count;
}

/** Calculate the difference in hours between now and a given date */
export function hoursAgo(dateString: string): number {
  const now = new Date();
  const date = new Date(dateString);
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
}

/** Check if a date string is today */
export function isToday(dateString: string): boolean {
  const date = new Date(dateString);
  const today = new Date();
  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  );
}

/** Get the sprint day label, e.g. 'Day 4 of 10' */
export function getSprintDayLabel(dayNumber: number, totalDays: number): string {
  return `Day ${dayNumber} of ${totalDays}`;
}

/** Generate an array of sprint day dates */
export function generateSprintDays(startDate: string, totalDays: number): string[] {
  const days: string[] = [];
  const current = new Date(startDate);
  let added = 0;

  while (added < totalDays) {
    const dayOfWeek = current.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      days.push(current.toISOString().split('T')[0]);
      added++;
    }
    current.setDate(current.getDate() + 1);
  }

  return days;
}
