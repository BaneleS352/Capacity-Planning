/** Planning scenario (what-if) types */

export interface PlanningScenario {
  id: string;
  name: string;
  assumptions: ScenarioAssumption[];
  result: ScenarioResult;
}

export interface ScenarioAssumption {
  id: string;
  type: 'remove-points' | 'add-capacity' | 'reduce-capacity' | 'member-unavailable' | 'support-rotation';
  label: string;
  value: number;
  memberId?: string;
  memberName?: string;
}

export interface ScenarioResult {
  adjustedCapacityPersonDays: number;
  adjustedCommittedPoints: number;
  adjustedUtilisationPercent: number;
  adjustedRiskLevel: 'high' | 'medium' | 'low';
  recommendedLoad: number;
  suggestedAction: string;
  constrainedRole: string | null;
}
