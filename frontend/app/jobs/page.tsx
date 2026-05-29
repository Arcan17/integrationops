"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import StatusBadge from "@/components/StatusBadge";
import { apiGet, Job } from "@/lib/api";

export default function JobsPage() {
  const [rows, setRows] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Job[]>("/jobs")
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <Shell>
      <h1>Jobs</h1>
      <p className="subtitle">Asynchronous processing jobs and retries</p>
      {error && <div className="error">{error}</div>}
      {rows && rows.length === 0 && <div className="empty">No jobs yet.</div>}
      {rows && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Status</th>
              <th>Attempts</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((j) => (
              <tr key={j.id}>
                <td>#{j.id}</td>
                <td>{j.job_type}</td>
                <td>
                  <StatusBadge status={j.status} />
                </td>
                <td>
                  {j.attempts}/{j.max_attempts}
                </td>
                <td className="muted">
                  {j.result ? JSON.stringify(j.result) : j.last_error ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Shell>
  );
}
