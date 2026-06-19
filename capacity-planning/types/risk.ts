/** Risk signal domain types */

export type RiskSeverity = 'high' | 'medium' | 'low';

export type RiskType =
  | 'over-utilisation'
  | 'leave-impact'
  | 'scope-creep'
  | 'blocked-work'
  | 'role-coverage'
  | 'carry-over'
  | 'stale-data'
  | 'unassigned-work';

export interface RiskSignal {
  id: string;
  severity: RiskSeverity;
  type: RiskType;
  title: string;
  whyItMatters: string;
  contributingFactors: string[];
  recommendation: string;
}

export interface RecommendedAction {
  id: string;
  priority: 'urgent' | 'recommended' | 'optional';
  action: string;
  expectedImpact: string;
  relatedRiskId: string;
}
