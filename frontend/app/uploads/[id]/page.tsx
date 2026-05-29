"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import StatusBadge from "@/components/StatusBadge";
import { apiGet, UploadBatch, ValidationError } from "@/lib/api";

export default function UploadErrorsPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [batch, setBatch] = useState<UploadBatch | null>(null);
  const [errors, setErrors] = useState<ValidationError[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiGet<UploadBatch>(`/uploads/${id}`),
      apiGet<ValidationError[]>(`/uploads/${id}/errors`),
    ])
      .then(([b, e]) => {
        setBatch(b);
        setErrors(e);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  return (
    <Shell>
      <p>
        <Link href="/uploads">← Back to uploads</Link>
      </p>
      <h1>Batch #{id}</h1>
      {batch && (
        <p className="subtitle">
          Status <StatusBadge status={batch.status} /> · {batch.total_files} file(s)
        </p>
      )}
      {error && <div className="error">{error}</div>}
      {errors && errors.length === 0 && (
        <div className="empty">No validation errors — all rows are valid. ✅</div>
      )}
      {errors && errors.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Column</th>
              <th>Code</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {errors.map((e) => (
              <tr key={e.id}>
                <td>{e.row_number ?? "—"}</td>
                <td>{e.column_name ?? "—"}</td>
                <td>
                  <span className="badge err">{e.error_code}</span>
                </td>
                <td>{e.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Shell>
  );
}
