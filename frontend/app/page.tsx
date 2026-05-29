"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { apiGet, Job, UploadBatch, ExportJob } from "@/lib/api";

interface Metrics {
  uploads: number;
  jobs: number;
  jobsSucceeded: number;
  jobsFailed: number;
  exports: number;
}

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [uploads, jobs, exports] = await Promise.all([
          apiGet<UploadBatch[]>("/uploads"),
          apiGet<Job[]>("/jobs"),
          apiGet<ExportJob[]>("/exports"),
        ]);
        setMetrics({
          uploads: uploads.length,
          jobs: jobs.length,
          jobsSucceeded: jobs.filter((j) => j.status === "succeeded").length,
          jobsFailed: jobs.filter((j) => j.status === "failed").length,
          exports: exports.length,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      }
    }
    load();
  }, []);

  return (
    <Shell>
      <h1>Overview</h1>
      <p className="subtitle">Operational snapshot of the IntegrationOps platform</p>
      {error && <div className="error">{error}</div>}
      {!metrics && !error && <p className="muted">Loading…</p>}
      {metrics && (
        <div className="cards">
          <div className="card">
            <div className="label">Upload batches</div>
            <div className="value">{metrics.uploads}</div>
          </div>
          <div className="card">
            <div className="label">Jobs</div>
            <div className="value">{metrics.jobs}</div>
          </div>
          <div className="card">
            <div className="label">Jobs succeeded</div>
            <div className="value">{metrics.jobsSucceeded}</div>
          </div>
          <div className="card">
            <div className="label">Jobs failed</div>
            <div className="value">{metrics.jobsFailed}</div>
          </div>
          <div className="card">
            <div className="label">Exports</div>
            <div className="value">{metrics.exports}</div>
          </div>
        </div>
      )}
    </Shell>
  );
}
