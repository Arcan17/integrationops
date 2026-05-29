"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Shell from "@/components/Shell";
import StatusBadge from "@/components/StatusBadge";
import { apiGet, UploadBatch } from "@/lib/api";

export default function UploadsPage() {
  const [rows, setRows] = useState<UploadBatch[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<UploadBatch[]>("/uploads")
      .then(setRows)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <Shell>
      <h1>Uploads</h1>
      <p className="subtitle">Ingested CSV/XLSX batches</p>
      {error && <div className="error">{error}</div>}
      {rows && rows.length === 0 && <div className="empty">No uploads yet.</div>}
      {rows && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Files</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((b) => (
              <tr key={b.id}>
                <td>#{b.id}</td>
                <td>
                  <StatusBadge status={b.status} />
                </td>
                <td>{b.total_files}</td>
                <td className="muted">{new Date(b.created_at).toLocaleString()}</td>
                <td>
                  <Link href={`/uploads/${b.id}`}>View errors →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Shell>
  );
}
