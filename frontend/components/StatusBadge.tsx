// Maps an API status string to a colored badge.
const OK = ["validated", "succeeded", "completed", "valid", "delivered", "active"];
const WARN = ["validating", "running", "queued", "retrying", "pending", "received"];

export default function StatusBadge({ status }: { status: string }) {
  let cls = "err";
  if (OK.includes(status)) cls = "ok";
  else if (WARN.includes(status)) cls = "warn";
  return <span className={`badge ${cls}`}>{status}</span>;
}
