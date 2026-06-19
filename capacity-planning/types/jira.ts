/** Jira issue domain types */

export type IssueStatus = 'To Do' | 'In Progress' | 'In Review' | 'QA' | 'Done' | 'Blocked';

export type IssuePriority = 'Critical' | 'High' | 'Medium' | 'Low';

export type IssueType = 'Story' | 'Bug' | 'Task' | 'Tech Debt' | 'Spike' | 'Sub-task';

export interface JiraIssue {
  id: string;
  key: string;
  title: string;
  assignee: string | null;
  assigneeId: string | null;
  status: IssueStatus;
  priority: IssuePriority;
  epic: string;
  issueType: IssueType;
  storyPoints: number;
  blocked: boolean;
  blockedReason?: string;
  carryOver: boolean;
  addedAfterSprintStart: boolean;
  dueDate: string | null;
  daysInStatus: number;
  labels: string[];
}
