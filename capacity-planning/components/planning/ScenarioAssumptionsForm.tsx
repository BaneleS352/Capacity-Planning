'use client';

import type { ScenarioAssumption } from '@/types/planning';

interface ScenarioAssumptionsFormProps {
  assumptions: ScenarioAssumption[];
  onChange: (id: string, value: number) => void;
  onReset: () => void;
}

export function ScenarioAssumptionsForm({
  assumptions,
  onChange,
  onReset,
}: ScenarioAssumptionsFormProps) {
  return (
    <section className="rounded-lg border border-border bg-white">
      <div className="flex items-center justify-between gap-3 border-b border-border p-4">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">Scenario Assumptions</h2>
          <p className="mt-1 text-sm text-text-secondary">Capacity and scope adjustments</p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-border px-3 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-sunken hover:text-text-primary focus-ring"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M2.5 5A4.5 4.5 0 1 1 3 9.5" />
            <path d="M2.5 2.5V5h2.5" />
          </svg>
          Reset
        </button>
      </div>

      <div className="divide-y divide-border">
        {assumptions.map(assumption => (
          <div key={assumption.id} className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <label htmlFor={assumption.id} className="text-sm font-medium text-text-primary">
                  {assumption.label}
                </label>
                {assumption.memberName && (
                  <p className="mt-1 text-xs text-text-tertiary">{assumption.memberName}</p>
                )}
              </div>
              <input
                id={`${assumption.id}-number`}
                type="number"
                min={0}
                max={40}
                value={assumption.value}
                onChange={event => onChange(assumption.id, Number(event.target.value))}
                className="h-8 w-20 rounded-lg border border-border px-2 text-right text-sm tabular-nums focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
            <input
              id={assumption.id}
              type="range"
              min={0}
              max={assumption.type === 'remove-points' ? 30 : 15}
              value={assumption.value}
              onChange={event => onChange(assumption.id, Number(event.target.value))}
              className="mt-3 w-full accent-[var(--color-accent)]"
            />
          </div>
        ))}
      </div>
    </section>
  );
}
