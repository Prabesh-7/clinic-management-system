"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, type CurrentUser } from "@/lib/api/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    const token = window.sessionStorage.getItem("access_token");
    if (!token) {
      router.replace("/");
      return;
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => router.replace("/"));
  }, [router]);

  function logout() {
    window.sessionStorage.removeItem("access_token");
    window.sessionStorage.removeItem("current_user_role");
    router.replace("/");
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <button
          type="button"
          onClick={logout}
          className="rounded-md border border-zinc-300 px-4 py-2"
        >
          Logout
        </button>
      </header>

      {user ? (
        <section className="rounded-xl border border-zinc-200 p-6">
          <p className="text-lg font-medium">{user.full_name}</p>
          <p className="mt-1 text-sm text-zinc-600">
            Username: {user.username}
          </p>
          <p className="mt-1 text-sm text-zinc-600">Role: {user.role}</p>
        </section>
      ) : (
        <p>Loading account...</p>
      )}
    </main>
  );
}
