"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { apiGet, AuditLog } from "@/lib/api";

export default function AuditPage() {
  const [rows, setRows] = useState<AuditLog[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<AuditLog[]>("/audit-logs?limit=100")
      .then(setRows)
      .catch((e) =>
        setError(
          e.message.includes("403")
            ? "Audit logs are restricted to admin users."
            : e.message,
        ),
      );
  }, []);

  return (
    <Shell>
      <h1>Audit logs</h1>
      <p className="subtitle">Operational event trail (admin only)</p>
      {error && <div className="error">{error}</div>}
      {rows && rows.length === 0 && <div className="empty">No audit events yet.</div>}
      {rows && rows.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Action</th>
              <th>Entity</th>
              <th>Actor</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td>#{a.id}</td>
                <td>
                  <span className="badge">{a.action}</span>
                </td>
                <td className="muted">
                  {a.entity_type ? `${a.entity_type} #${a.entity_id ?? "—"}` : "—"}
                </td>
                <td className="muted">{a.actor_id ?? "—"}</td>
                <td className="muted">{new Date(a.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Shell>
  );
}
