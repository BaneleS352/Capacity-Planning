'use client';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { Sprint } from '@/types/dashboard';
import type { BurndownPoint } from '@/types/sprint';
import styles from './SprintBurndownChart.module.css';

interface SprintBurndownChartProps {
  sprint: Sprint;
  points: BurndownPoint[];
}

const WIDTH = 720;
const HEIGHT = 300;
const PADDING = 36;

export function SprintBurndownChart({ sprint, points }: SprintBurndownChartProps) {
  const maxValue = Math.max(...points.flatMap(point => [point.ideal, point.actual ?? 0]), 1);
  const idealPath = points.map((point, index) => toPoint(point.ideal, index, points.length, maxValue)).join(' ');
  const actualPoints = points
    .map((point, index) => point.actual === null ? null : toPoint(point.actual, index, points.length, maxValue))
    .filter((point): point is string => point !== null);
  const latestActual = [...points].reverse().find(point => point.actual !== null);
  const latestIdeal = latestActual ? points.find(point => point.day === latestActual.day)?.ideal ?? 0 : 0;
  const variance = latestActual ? latestActual.actual! - latestIdeal : 0;

  return (
    <Card>
      <div className={styles.container}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Sprint Burndown</h2>
            <p className={styles.subtitle}>{sprint.name} ideal vs actual remaining work</p>
          </div>
          <Badge variant={variance > 8 ? 'amber' : 'green'}>
            {variance > 0 ? `+${Math.round(variance)} SP` : `${Math.round(variance)} SP`}
          </Badge>
        </div>

        <div className={styles.chartScroll}>
          <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className={styles.svg} role="img" aria-label="Sprint burndown chart">
            <line x1={PADDING} y1={HEIGHT - PADDING} x2={WIDTH - PADDING} y2={HEIGHT - PADDING} className={styles.axis} />
            <line x1={PADDING} y1={PADDING} x2={PADDING} y2={HEIGHT - PADDING} className={styles.axis} />

            {[0, 0.25, 0.5, 0.75, 1].map(tick => {
              const y = PADDING + (1 - tick) * (HEIGHT - PADDING * 2);
              return (
                <g key={tick}>
                  <line x1={PADDING} y1={y} x2={WIDTH - PADDING} y2={y} className={styles.gridLine} />
                  <text x={PADDING - 10} y={y + 4} textAnchor="end" className={styles.tickText}>
                    {Math.round(maxValue * tick)}
                  </text>
                </g>
              );
            })}

            <polyline
              points={idealPath}
              className={styles.idealLine}
            />
            <polyline
              points={actualPoints.join(' ')}
              className={styles.actualLine}
            />

            {points.map((point, index) => {
              const [x, y] = toPointTuple(point.ideal, index, points.length, maxValue);
              return (
                <g key={point.day}>
                  <text x={x} y={HEIGHT - 10} textAnchor="middle" className={styles.tickText}>{point.day}</text>
                  {point.actual !== null && (
                    <circle
                      cx={toPointTuple(point.actual, index, points.length, maxValue)[0]}
                      cy={toPointTuple(point.actual, index, points.length, maxValue)[1]}
                      r="4"
                      className={styles.actualPoint}
                    />
                  )}
                  <circle cx={x} cy={y} r="2.5" className={styles.idealPoint} />
                </g>
              );
            })}
          </svg>
        </div>

        <div className={styles.legend}>
          <span className={styles.legendItem}><span className={styles.legendActualColor} />Actual</span>
          <span className={styles.legendItem}><span className={styles.legendIdealColor} />Ideal</span>
        </div>
      </div>
    </Card>
  );
}

function toPoint(value: number, index: number, count: number, maxValue: number) {
  const [x, y] = toPointTuple(value, index, count, maxValue);
  return `${x},${y}`;
}

function toPointTuple(value: number, index: number, count: number, maxValue: number) {
  const chartWidth = WIDTH - PADDING * 2;
  const chartHeight = HEIGHT - PADDING * 2;
  const x = PADDING + (index / Math.max(count - 1, 1)) * chartWidth;
  const y = PADDING + (1 - value / maxValue) * chartHeight;
  return [x, y] as const;
}
