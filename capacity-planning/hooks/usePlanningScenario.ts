'use client';

import { useMemo, useState } from 'react';
import { calculateRecommendedLoad } from '@/lib/capacityUtils';
import type { CapacitySummary } from '@/types/dashboard';
import type { PlanningScenario, ScenarioAssumption, ScenarioResult } from '@/types/planning';

const INITIAL_ASSUMPTIONS: ScenarioAssumption[] = [
  {
    id: 'remove-non-critical',
    type: 'remove-points',
    label: 'Defer non-critical story points',
    value: 10,
  },
  {
    id: 'qa-support',
    type: 'add-capacity',
    label: 'Add QA backup person-days',
    value: 2,
    memberName: 'Cross-trained developer',
  },
  {
    id: 'support-rotation',
    type: 'reduce-capacity',
    label: 'Support rotation capacity cost',
    value: 3,
    memberName: 'K. Govender',
  },
  {
    id: 'unplanned-leave',
    type: 'member-unavailable',
    label: 'Additional unavailable person-days',
    value: 0,
  },
];

export function usePlanningScenario(capacitySummary: CapacitySummary) {
  const [assumptions, setAssumptions] = useState<ScenarioAssumption[]>(INITIAL_ASSUMPTIONS);

  const result = useMemo<ScenarioResult>(() => {
    const removedPoints = sumAssumptions(assumptions, 'remove-points');
    const addedCapacity = sumAssumptions(assumptions, 'add-capacity');
    const reducedCapacity =
      sumAssumptions(assumptions, 'reduce-capacity') +
      sumAssumptions(assumptions, 'member-unavailable') +
      sumAssumptions(assumptions, 'support-rotation');
    const adjustedCapacityPersonDays = Math.max(
      0,
      capacitySummary.availablePersonDays + addedCapacity - reducedCapacity,
    );
    const adjustedCommittedPoints = Math.max(
      0,
      capacitySummary.committedStoryPointEquivalent - removedPoints,
    );
    const adjustedUtilisationPercent = adjustedCapacityPersonDays === 0
      ? 0
      : Math.round((adjustedCommittedPoints / adjustedCapacityPersonDays) * 100);
    const adjustedRiskLevel = adjustedUtilisationPercent > 100
      ? 'high'
      : adjustedUtilisationPercent > 85
        ? 'medium'
        : 'low';
    const recommendedLoad = calculateRecommendedLoad(adjustedCapacityPersonDays);
    const pointsToRemove = Math.max(0, adjustedCommittedPoints - recommendedLoad);

    return {
      adjustedCapacityPersonDays,
      adjustedCommittedPoints,
      adjustedUtilisationPercent,
      adjustedRiskLevel,
      recommendedLoad,
      suggestedAction: adjustedRiskLevel === 'high'
        ? `Remove ${pointsToRemove} more story points or add capacity before sprint close.`
        : adjustedRiskLevel === 'medium'
          ? 'Hold current scope and protect QA validation capacity.'
          : 'Current assumptions bring the sprint inside the target range.',
      constrainedRole: adjustedRiskLevel === 'high' ? 'QA Engineer' : null,
    };
  }, [assumptions, capacitySummary]);

  const scenario: PlanningScenario = {
    id: 'sprint-24-6-what-if',
    name: 'Sprint 24.6 recovery scenario',
    assumptions,
    result,
  };

  const updateAssumption = (id: string, value: number) => {
    setAssumptions(current =>
      current.map(assumption =>
        assumption.id === id ? { ...assumption, value } : assumption,
      ),
    );
  };

  const resetScenario = () => {
    setAssumptions(INITIAL_ASSUMPTIONS);
  };

  return {
    scenario,
    updateAssumption,
    resetScenario,
  };
}

function sumAssumptions(assumptions: ScenarioAssumption[], type: ScenarioAssumption['type']) {
  return assumptions
    .filter(assumption => assumption.type === type)
    .reduce((total, assumption) => total + assumption.value, 0);
}
