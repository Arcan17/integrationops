"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import StatusBadge from "@/components/StatusBadge";
import { apiGet, downloadExport, ExportJob } from "@/lib/api";

export default function ExportsPage() {
  const [rows, setRows] = useState<ExportJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<ExportJob[]>("/exports")
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);

  async function download(e: ExportJob) {
    try {
      await downloadExport(e.id, `export_${e.id}.${e.export_format}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    }
  }

  return (
    <Shell>
      <h1>Exports</h1>
      <p className="subtitle">Generated CSV/XLSX exports</p>
      {error && <div className="error">{error}</div>}
      {rows && rows.length === 0 && <div className="empty">No exports yet.</div>}
      {rows && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Format</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id}>
                <td>#{e.id}</td>
                <td>{e.export_format.toUpperCase()}</td>
                <td>
                  <StatusBadge status={e.status} />
                </td>
                <td className="muted">{new Date(e.created_at).toLocaleString()}</td>
                <td>
                  <button
                    className="btn small"
                    disabled={e.status !== "completed"}
                    onClick={() => download(e)}
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Shell>
  );
}
