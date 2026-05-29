"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/api";

export default function Nav() {
  const router = useRouter();

  function logout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <nav className="nav">
      <span className="brand">IntegrationOps</span>
      <Link href="/">Overview</Link>
      <Link href="/uploads">Uploads</Link>
      <Link href="/jobs">Jobs</Link>
      <Link href="/exports">Exports</Link>
      <Link href="/audit">Audit</Link>
      <span className="spacer" />
      <button onClick={logout}>Log out</button>
    </nav>
  );
}
