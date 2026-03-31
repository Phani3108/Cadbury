import { Briefcase } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";

export default function OpportunitiesPage() {
  return (
    <div>
      <PageHeader
        title="Opportunities"
        subtitle="All job opportunities your delegate has processed"
      />
      <div className="bg-white border border-slate-200 rounded-lg">
        <EmptyState
          icon={Briefcase}
          title="No opportunities yet"
          description="Your delegate will populate this list as it screens incoming recruiter emails"
        />
      </div>
    </div>
  );
}
