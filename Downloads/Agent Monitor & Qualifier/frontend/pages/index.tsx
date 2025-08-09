import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "../lib/api";
import { fetchAuth } from "../lib/auth";

type Run = { run_id:string; agent:string; environment:string; tenant?:string; created_at?:string;
  certified?:boolean; scores?:{overall:number}; tags?:string[] };

export default function Runs() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [filter, setFilter] = useState<any>({ q:"", certified:"any", tag:"", agent:"", env:"" });
  const [views, setViews] = useState<any>({ views: [] });

  useEffect(() => {
    fetchAuth(`${API_BASE}/runs`).then(r=>r.json()).then(setRuns).catch(()=>{});
    fetchAuth(`${API_BASE}/views`).then(r=>r.json()).then(setViews).catch(()=>{});
  }, []);

  const shown = useMemo(() => {
    return runs.filter(r => {
      if (filter.agent && r.agent !== filter.agent) return false;
      if (filter.env && r.environment !== filter.env) return false;
      if (filter.tag && !(r.tags||[]).includes(filter.tag)) return false;
      if (filter.certified === "yes" && !r.certified) return false;
      if (filter.certified === "no" && r.certified) return false;
      if (filter.q && !(`${r.run_id} ${r.agent}`.toLowerCase().includes(filter.q.toLowerCase()))) return false;
      return true;
    });
  }, [runs, filter]);

  async function saveView() {
    const id = prompt("View id (slug):") || ""; if (!id) return;
    const name = prompt("View name:") || id;
    await fetchAuth(`${API_BASE}/views`, { method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ id, name, query: filter }) });
    const j = await (await fetchAuth(`${API_BASE}/views`)).json(); setViews(j);
  }

  return (
    <div className="container">
      <div className="h1">Runs</div>
      <div className="card" style={{display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:8}}>
        <input placeholder="Search id/agent" value={filter.q} onChange={e=>setFilter({...filter,q:e.target.value})}/>
        <select value={filter.certified} onChange={e=>setFilter({...filter,certified:e.target.value})}>
          <option value="any">cert:any</option><option value="yes">cert:yes</option><option value="no">cert:no</option>
        </select>
        <input placeholder="agent" value={filter.agent} onChange={e=>setFilter({...filter,agent:e.target.value})}/>
        <input placeholder="env" value={filter.env} onChange={e=>setFilter({...filter,env:e.target.value})}/>
        <input placeholder="tag" value={filter.tag} onChange={e=>setFilter({...filter,tag:e.target.value})}/>
        <button onClick={saveView}>Save view</button>
      </div>

      {views.views?.length>0 && (
        <div className="card">
          <strong>Saved views</strong>
          <ul>{views.views.map((v:any)=>(
            <li key={v.id}><a className="link" href="#"
              onClick={(e)=>{e.preventDefault(); setFilter(v.query);}}>{v.name}</a></li>
          ))}</ul>
        </div>
      )}

      <div className="card">
        <table className="table">
          <thead><tr><th>ID</th><th>Agent</th><th>Env</th><th>Tenant</th><th>Score</th><th>Cert</th><th>Tags</th></tr></thead>
          <tbody>
            {shown.map(r=>(
              <tr key={r.run_id}>
                <td><a className="link" href={`/run/${r.run_id}`}>{r.run_id.slice(0,8)}</a></td>
                <td>{r.agent}</td><td>{r.environment}</td><td>{r.tenant||"default"}</td>
                <td>{r.scores?.overall ?? "-"}</td>
                <td>{r.certified ? "✅" : "—"}</td>
                <td>{(r.tags||[]).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
