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
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <form
        className="w-full max-w-md rounded-xl border border-zinc-200 bg-white p-8 shadow-sm"
        onSubmit={handleSubmit}
        aria-busy={loading}
      >
        <p className="text-sm font-medium text-zinc-500">
          Clinic Management System
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950">
          Sign in to your account
        </h1>
        <p className="mt-2 mb-8 text-sm text-zinc-600">
          Enter your clinic account details to continue.
        </p>

        <label className="mb-5 block">
          <span className="mb-2 block text-sm font-medium text-zinc-700">
            Username
          </span>
          <input
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Your username"
            autoComplete="username"
            required
          />
        </label>

        <label className="mb-6 block">
          <span className="mb-2 block text-sm font-medium text-zinc-700">
            Password
          </span>
          <input
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Your password"
            autoComplete="current-password"
            required
          />
        </label>

        <button
          className="w-full rounded-md bg-zinc-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-600 disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={loading}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        {message ? (
          <p
            className="mt-4 text-sm text-zinc-700"
            role="alert"
            aria-live="polite"
          >
            {message}
          </p>
        ) : null}
      </form>
    </main>
  );
}
