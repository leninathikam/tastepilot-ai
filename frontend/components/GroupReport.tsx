import { Result } from '../lib/types';

export function GroupReport({ result }: { result: Result }) {
  const group = result.group;
  if (!group) return null;
  const all = [...result.itinerary, ...result.alternatives];
  const name = (id: string) => all.find((c) => c.id === id)?.name || id;
  const sameChoice =
    [...group.selected_ids].sort().join(',') === [...group.mean_objective.ids].sort().join(',');

  const isModal = group.engine === 'modal';

  return (
    <section className="group-report" aria-labelledby="compromise-title">
      <div className="eyebrow-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
        <div className="eyebrow" style={{ margin: 0 }}>A thoughtful compromise</div>
        <span
          className={`engine-pill ${isModal ? 'modal' : 'local'}`}
          style={{
            fontSize: '0.75rem',
            padding: '2px 8px',
            borderRadius: '12px',
            fontWeight: 600,
            letterSpacing: '0.02em',
            background: isModal ? 'rgba(59, 130, 246, 0.15)' : 'rgba(107, 114, 128, 0.15)',
            color: isModal ? '#60a5fa' : '#9ca3af',
            border: isModal ? '1px solid rgba(96, 165, 250, 0.3)' : '1px solid rgba(156, 163, 175, 0.3)',
          }}
          title={group.fallback_reason ? `Fallback: ${group.fallback_reason}` : isModal ? 'Computed via Modal Serverless Intelligence' : 'Computed via Local Engine'}
        >
          {isModal ? '⚡ Modal Serverless' : 'Local Engine'}
        </span>
      </div>

      <h3 id="compromise-title">A day everyone has a part in.</h3>
      <p>
        {group.is_provisional
          ? 'These are provisional group discoveries. Prices and visit details still need checking.'
          : 'The planner balances each profile’s strongest represented interest across the selected stops.'}{' '}
        {result.mode === 'fixture' ? 'All taste signals here are synthetic examples.' : ''}
      </p>

      <div className="coverage-grid">
        {Object.entries(group.fair.member_coverage).map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value.toFixed(2)}</strong>
            <div className="coverage-bar">
              <i style={{ width: `${value * 100}%` }} />
            </div>
            <small>Modeled best-stop coverage</small>
          </div>
        ))}
      </div>

      <p className="group-disclaimer">
        These numbers are relative algorithmic proxies, not satisfaction percentages or a prediction about a person.
      </p>

      <p className="tradeoff-summary">
        {sameChoice
          ? 'Both objectives chose the same places. There is no different compromise to claim for this result.'
          : 'The objectives chose different places. Compare who gains representation and who gives some up below.'}
      </p>

      <table className="tradeoff-table">
        <caption>Each person’s best-stop coverage, on the same candidate pool</caption>
        <thead>
          <tr>
            <th scope="col">Person</th>
            <th scope="col">Mean choice</th>
            <th scope="col">Fair choice</th>
            <th scope="col">Change</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(group.fair.member_coverage).map(([label, value]) => {
            const average = group.mean_objective.member_coverage[label] ?? 0;
            const delta = value - average;
            return (
              <tr key={label}>
                <th scope="row">{label}</th>
                <td>{average.toFixed(2)}</td>
                <td>{value.toFixed(2)}</td>
                <td>
                  {delta > 0 ? '+' : ''}
                  {delta.toFixed(2)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {group.counterfactuals && group.counterfactuals.length > 0 && (
        <div
          className="counterfactual-block"
          style={{
            margin: '1.25rem 0',
            padding: '1rem',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>Who shaped this compromise?</h4>
            <span style={{ fontSize: '0.75rem', color: '#888' }}>Leave-one-member-out analysis</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
            {group.counterfactuals.map((cf) => (
              <div
                key={cf.excluded_member}
                style={{
                  padding: '0.6rem 0.8rem',
                  borderRadius: '6px',
                  background: cf.changed ? 'rgba(59, 130, 246, 0.06)' : 'rgba(255, 255, 255, 0.02)',
                  border: cf.changed ? '1px solid rgba(59, 130, 246, 0.2)' : '1px solid rgba(255, 255, 255, 0.04)',
                  fontSize: '0.85rem',
                  lineHeight: '1.4',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <strong>Without {cf.excluded_member}:</strong>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      padding: '1px 6px',
                      borderRadius: '4px',
                      background: cf.changed ? 'rgba(59, 130, 246, 0.2)' : 'rgba(156, 163, 175, 0.15)',
                      color: cf.changed ? '#93c5fd' : '#9ca3af',
                    }}
                  >
                    {cf.changed ? 'Shifts compromise' : 'Aligned with group'}
                  </span>
                </div>
                <div style={{ color: '#ccc', fontSize: '0.8rem' }}>{cf.explanation}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {group.modeled_profiles < group.party_size && (
        <p className="warning">
          Only {group.modeled_profiles} of {group.party_size} people have taste profiles. The remaining people’s
          preferences are not modeled.
        </p>
      )}

      <div className="group-choices">
        <div>
          <h4>Balanced compromise</h4>
          <p>{group.selected_ids.map(name).join(' · ') || 'No eligible options'}</p>
        </div>
        <div>
          <h4>Mean-coverage alternative</h4>
          <p>{group.mean_objective.ids.map(name).join(' · ') || 'No eligible options'}</p>
        </div>
      </div>

      <details>
        <summary>Inspect the tradeoff and source trail</summary>
        <p>{group.strategy}</p>
        <p>
          Least-served coverage change versus mean objective:{' '}
          {group.minimum_coverage_delta >= 0 ? '+' : ''}
          {group.minimum_coverage_delta.toFixed(2)}. Mean coverage tradeoff:{' '}
          {group.mean_coverage_tradeoff.toFixed(2)}. {group.fair.subsets_examined} subsets inspected.
        </p>
        {group.modal_metrics && (
          <p style={{ color: '#93c5fd', fontSize: '0.8rem' }}>
            Modal Serverless execution: {group.modal_metrics.execution_ms ?? 0}ms engine time
            {group.modal_metrics.roundtrip_ms ? ` (${group.modal_metrics.roundtrip_ms}ms roundtrip)` : ''}
          </p>
        )}
        <p>
          Without taste signals, using the same pool and constraints:{' '}
          {group.without_taste.ids.map(name).join(' · ') || 'No eligible options'}.
        </p>
        {group.profiles.map((p) => (
          <p key={p.label}>
            <b>{p.label}</b>: {p.seeds.map((s) => `${s.name} (${s.category})`).join(', ')} →{' '}
            {p.resolved_ids.join(', ')}
          </p>
        ))}
        <p>{group.disclaimer}</p>
      </details>
    </section>
  );
}
