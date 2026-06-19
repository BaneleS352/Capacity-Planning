/** Risk signal generation and sorting utilities */

import { RISK_SEVERITY_ORDER } from '@/constants/riskLevels';
import type { RiskSignal, RiskSeverity } from '@/types/risk';

/** Sort risk signals by severity (high first) */
export function sortRisksBySeverity(risks: RiskSignal[]): RiskSignal[] {
  return [...risks].sort((a, b) => {
    return RISK_SEVERITY_ORDER.indexOf(a.severity) - RISK_SEVERITY_ORDER.indexOf(b.severity);
  });
}

/** Count risks by severity */
export function countRisksBySeverity(risks: RiskSignal[]): Record<RiskSeverity, number> {
  return {
    high: risks.filter(r => r.severity === 'high').length,
    medium: risks.filter(r => r.severity === 'medium').length,
    low: risks.filter(r => r.severity === 'low').length,
  };
}

/** Get the highest severity from a list of risks */
export function getHighestSeverity(risks: RiskSignal[]): RiskSeverity {
  if (risks.some(r => r.severity === 'high')) return 'high';
  if (risks.some(r => r.severity === 'medium')) return 'medium';
  return 'low';
}

/** Count total active risk signals */
export function countActiveSignals(risks: RiskSignal[]): number {
  return risks.length;
}
