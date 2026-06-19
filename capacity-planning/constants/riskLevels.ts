/** Risk level definitions, labels, and display properties */

import type { RiskSeverity } from '@/types/risk';

export interface RiskLevelConfig {
  severity: RiskSeverity;
  label: string;
  description: string;
  sortOrder: number;
}

export const RISK_LEVEL_CONFIG: Record<RiskSeverity, RiskLevelConfig> = {
  high: {
    severity: 'high',
    label: 'High',
    description: 'Immediate attention required. Delivery risk is significant.',
    sortOrder: 0,
  },
  medium: {
    severity: 'medium',
    label: 'Medium',
    description: 'Monitor closely. Capacity pressure detected.',
    sortOrder: 1,
  },
  low: {
    severity: 'low',
    label: 'Low',
    description: 'Healthy. Minor items to watch.',
    sortOrder: 2,
  },
};

export const RISK_SEVERITY_ORDER: RiskSeverity[] = ['high', 'medium', 'low'];
