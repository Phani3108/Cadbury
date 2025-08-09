import { useEffect, useState } from "react";
import VerifyRun from "../../aah/frontend/app/components/VerifyRun";
import DeterminismCard from "./DeterminismCard";
import TagEditor from "./run/TagEditor";

export default function RunDetails({ runId }: { runId: string }) {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/runs/${runId}`)
      .then((response) => response.json())
      .then((data) => setSummary(data));
  }, [runId]);

  return (
    <div>
      {/* ...other run details... */}
      {summary && (
        <TagEditor runId={runId} initialTags={summary.tags || []} />
      )}
      <VerifyRun runId={runId} />
      <DeterminismCard runId={runId} />
    </div>
  );
}
