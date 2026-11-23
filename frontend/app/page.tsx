"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { getCurrentUser, login } from "@/lib/api/auth";

export default function HomePage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const response = await login({ username, password });
      window.sessionStorage.setItem("access_token", response.access_token);
      const user = await getCurrentUser();
      window.sessionStorage.setItem("current_user_role", user.role);
      setMessage(`Signed in as ${user.full_name} (${user.role})`);
      router.push("/dashboard");
    } catch (error) {
      setMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to connect to the server",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <form
        className="w-full rounded-xl border border-zinc-200 bg-white p-6 shadow-sm"
        onSubmit={handleSubmit}
      >
        <h1 className="mb-6 text-2xl font-semibold">Clinic login</h1>

        <label className="mb-4 block">
          <span className="mb-1 block text-sm font-medium">Username</span>
          <input
            className="w-full rounded-md border border-zinc-300 px-3 py-2"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </label>

        <label className="mb-5 block">
          <span className="mb-1 block text-sm font-medium">Password</span>
          <input
            className="w-full rounded-md border border-zinc-300 px-3 py-2"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        <button
          className="w-full rounded-md bg-zinc-950 px-4 py-2 font-medium text-white disabled:opacity-60"
          type="submit"
          disabled={loading}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        {message ? (
          <p className="mt-4 text-sm text-zinc-700" role="alert">
            {message}
          </p>
        ) : null}
      </form>
    </main>
  );
}
