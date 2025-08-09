import { useState, useEffect } from "react";

export default function DeterminismCard({ runId }: { runId: string }) {
  const [detStats, setDetStats] = useState<any[]>([]);
  const [reSamples, setReSamples] = useState<number>(20);
  const [reConc, setReConc] = useState<number>(5);
  const [rerunLoading, setRerunLoading] = useState(false);

  useEffect(() => {
    if (!runId) return;
    fetch(`/api/runs/${runId}/determinism/stats`).then(r=>r.json()).then(setDetStats).catch(()=>{});
  }, [runId]);

  async function rerunDet() {
    setRerunLoading(true);
    const res = await fetch(`/api/runs/${runId}/determinism/rerun`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ samples: reSamples, concurrency: reConc })
    });
    setRerunLoading(false);
    if (res.ok) {
      const j = await res.json();
      window.location.href = `/run/${j.run_id}`;
    }
  }

  if (detStats.length === 0) return null;

  return (
    <div className="card">
      <div className="h2">Determinism (Load)</div>
      <table className="table">
        <thead><tr>
          <th>Test</th><th>Pass</th><th>Det%</th><th>P50/P95/P99 (ms)</th><th>CV</th><th>Pass-rate</th><th>Samples×Conc</th>
        </tr></thead>
        <tbody>
          {detStats.map((r:any)=>(
            <tr key={r.id}>
              <td><code>{r.id}</code></td>
              <td>{r.passed ? "✅" : "❌"}</td>
              <td>{r.determinism_pct?.toFixed?.(1) ?? "-"}</td>
              <td>{r.latency_ms ? `${r.latency_ms.p50}/${r.latency_ms.p95}/${r.latency_ms.p99}` : "-"}</td>
              <td>{r.latency_ms ? r.latency_ms.cv : "-"}</td>
              <td>{r.pass_rate_pct?.toFixed?.(1) ?? "-"}</td>
              <td>{r.samples}×{r.concurrency}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ display:"flex", gap:12, alignItems:"center", marginTop:12 }}>
        <div className="small">Determinism rerun:</div>
        <label className="small">samples <input type="number" value={reSamples} onChange={e=>setReSamples(parseInt(e.target.value||"0"))} style={{width:80}}/></label>
        <label className="small">concurrency <input type="number" value={reConc} onChange={e=>setReConc(parseInt(e.target.value||"0"))} style={{width:80}}/></label>
        <button onClick={rerunDet} disabled={rerunLoading}>{rerunLoading ? "Running..." : "Run determinism only"}</button>
      </div>
    </div>
  );
}
