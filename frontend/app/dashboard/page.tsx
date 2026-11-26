"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { getCurrentUser, type CurrentUser } from "@/lib/api/auth";
import {
  getMyClinic,
  listClinics,
  type Clinic,
} from "@/lib/api/clinics";

type IconName =
  | "grid"
  | "building"
  | "user"
  | "logout"
  | "check"
  | "clock"
  | "alert";

const iconPaths: Record<IconName, ReactNode> = {
  grid: (
    <>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
    </>
  ),
  building: (
    <>
      <path d="M4 21V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v16" />
      <path d="M2 21h20M8 7h1m3 0h1M8 11h1m3 0h1m-5 4h1m3 0h1m2 6v-4h3v4" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 21a7 7 0 0 1 14 0" />
    </>
  ),
  logout: (
    <>
      <path d="M10 17l5-5-5-5m5 5H3" />
      <path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" />
    </>
  ),
  check: (
    <>
      <path d="m5 12 4 4L19 6" />
      <circle cx="12" cy="12" r="9" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  alert: (
    <>
      <path d="m10.3 4.3-7.5 13A2 2 0 0 0 4.5 20h15a2 2 0 0 0 1.7-2.7l-7.5-13a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4m0 3h.01" />
    </>
  ),
};

const statusPresentation: Record<
  Clinic["status"],
  { label: string; className: string }
> = {
  draft: {
    label: "Draft",
    className: "bg-slate-100 text-slate-600 ring-slate-200",
  },
  pending_verification: {
    label: "Pending review",
    className: "bg-amber-50 text-amber-700 ring-amber-200",
  },
  active: {
    label: "Active",
    className: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  },
  suspended: {
    label: "Suspended",
    className: "bg-rose-50 text-rose-700 ring-rose-200",
  },
  closed: {
    label: "Closed",
    className: "bg-slate-100 text-slate-600 ring-slate-200",
  },
};

function Icon({
  name,
  className = "size-5",
}: {
  name: IconName;
  className?: string;
}) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 24 24"
    >
      {iconPaths[name]}
    </svg>
  );
}

function getInitials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function MetricCard({
  icon,
  label,
  value,
  detail,
  tone,
}: {
  icon: IconName;
  label: string;
  value: number | string;
  detail: string;
  tone: "blue" | "green" | "amber" | "rose";
}) {
  const iconTone = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    rose: "bg-rose-50 text-rose-700",
  }[tone];

  return (
    <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/40">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
            {value}
          </p>
        </div>
        <span
          className={`inline-flex size-10 items-center justify-center rounded-xl ${iconTone}`}
        >
          <Icon name={icon} />
        </span>
      </div>
      <p className="mt-3 text-xs text-slate-500">{detail}</p>
    </article>
  );
}

function ClinicStatusBadge({ status }: { status: Clinic["status"] }) {
  const presentation = statusPresentation[status];

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${presentation.className}`}
    >
      {presentation.label}
    </span>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [clinics, setClinics] = useState<Clinic[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      const token = window.sessionStorage.getItem("access_token");
      if (!token) {
        router.replace("/");
        return;
      }

      let currentUser: CurrentUser;
      try {
        currentUser = await getCurrentUser();
      } catch {
        if (!cancelled) {
          router.replace("/");
        }
        return;
      }

      if (cancelled) {
        return;
      }
      setUser(currentUser);

      try {
        const clinicData =
          currentUser.role === "admin"
            ? await listClinics()
            : [await getMyClinic()];
        if (!cancelled) {
          setClinics(clinicData);
        }
      } catch (error) {
        if (!cancelled) {
          setLoadError(
            error instanceof ApiError
              ? error.message
              : "We couldn't load clinic information. Please try again.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [router]);

  function logout() {
    window.sessionStorage.removeItem("access_token");
    window.sessionStorage.removeItem("current_user_role");
    router.replace("/");
  }

  const isAdmin = user?.role === "admin";
  const activeClinics =
    clinics?.filter((clinic) => clinic.status === "active").length ?? 0;
  const pendingClinics =
    clinics?.filter((clinic) => clinic.status === "pending_verification").length ??
    0;
  const suspendedClinics =
    clinics?.filter((clinic) => clinic.status === "suspended").length ?? 0;
  const clinic = clinics?.[0];

  return (
    <main className="min-h-screen bg-[#f7f8fb] text-slate-900 lg:flex">
      <aside className="border-b border-slate-200 bg-white px-5 py-5 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col lg:border-r lg:border-b-0 lg:px-4 lg:py-6">
        <a
          className="flex items-center gap-3 rounded-xl px-2 py-1"
          href="#overview"
          aria-label="ClinicCare dashboard home"
        >
          <span className="flex size-10 items-center justify-center rounded-xl bg-blue-700 text-white shadow-sm shadow-blue-900/20">
            <Icon name="building" className="size-5" />
          </span>
          <span>
            <span className="block text-sm font-bold tracking-tight text-slate-950">
              ClinicCare
            </span>
            <span className="mt-0.5 block text-xs text-slate-500">
              Management portal
            </span>
          </span>
        </a>

        <p className="mb-3 mt-9 hidden px-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 lg:block">
          Workspace
        </p>
        <nav
          aria-label="Dashboard navigation"
          className="mt-5 flex gap-2 overflow-x-auto lg:mt-0 lg:flex-col"
        >
          <a
            className="inline-flex shrink-0 items-center gap-3 rounded-xl bg-blue-50 px-3 py-2.5 text-sm font-semibold text-blue-800 lg:w-full"
            href="#overview"
          >
            <Icon name="grid" className="size-[18px]" />
            Overview
          </a>
          {isAdmin ? (
            <a
              className="inline-flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 lg:w-full"
              href="#clinics"
            >
              <Icon name="building" className="size-[18px]" />
              Clinics
            </a>
          ) : null}
          <a
            className="inline-flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 lg:w-full"
            href="#account"
          >
            <Icon name="user" className="size-[18px]" />
            My account
          </a>
        </nav>

        <div className="mt-auto hidden border-t border-slate-100 pt-5 lg:block">
          <p className="px-3 text-xs leading-5 text-slate-400">
            A clearer view of your clinic operations.
          </p>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex min-h-[76px] items-center justify-between gap-4 border-b border-slate-200/80 bg-white px-5 sm:px-8 lg:px-10">
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-400">
              ClinicCare / Workspace
            </p>
            <p className="mt-1 truncate text-sm font-semibold text-slate-800">
              {isAdmin ? "Administrator workspace" : "Clinic workspace"}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {user ? (
              <div className="hidden text-right sm:block">
                <p className="max-w-48 truncate text-sm font-semibold text-slate-800">
                  {user.full_name}
                </p>
                <p className="mt-0.5 text-xs capitalize text-slate-500">
                  {user.role === "admin" ? "Administrator" : "Dental team"}
                </p>
              </div>
            ) : null}
            <span className="flex size-10 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-800">
              {user ? getInitials(user.full_name) : "…"}
            </span>
            <button
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
              type="button"
              onClick={logout}
            >
              <Icon name="logout" className="size-4" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 sm:py-10 lg:px-10">
          <section id="overview" aria-labelledby="page-title">
            <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
              <div>
                <p className="text-sm font-medium text-blue-700">
                  {isAdmin ? "Administration" : "Your clinic"}
                </p>
                <h1
                  className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2rem]"
                  id="page-title"
                >
                  {isLoading
                    ? "Workspace overview"
                    : `Welcome back${user ? `, ${user.full_name.split(" ")[0]}` : ""}`}
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                  {isAdmin
                    ? "Monitor clinic onboarding and keep your organization moving."
                    : "Review your clinic details and manage your account."}
                </p>
              </div>
              {user ? (
                <span className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
                  <span className="size-1.5 rounded-full bg-emerald-500" />
                  Account {user.status}
                </span>
              ) : null}
            </div>

            {loadError ? (
              <div
                className="mt-7 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
                role="alert"
              >
                <Icon name="alert" className="mt-0.5 size-5 shrink-0" />
                <p>{loadError}</p>
              </div>
            ) : null}

            {isAdmin ? (
              <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  icon="building"
                  label="Total clinics"
                  value={clinics ? clinics.length : "—"}
                  detail="Clinics in your organization"
                  tone="blue"
                />
                <MetricCard
                  icon="check"
                  label="Active"
                  value={clinics ? activeClinics : "—"}
                  detail="Verified and currently active"
                  tone="green"
                />
                <MetricCard
                  icon="clock"
                  label="Pending review"
                  value={clinics ? pendingClinics : "—"}
                  detail="Awaiting verification"
                  tone="amber"
                />
                <MetricCard
                  icon="alert"
                  label="Suspended"
                  value={clinics ? suspendedClinics : "—"}
                  detail="Clinics currently suspended"
                  tone="rose"
                />
              </div>
            ) : null}
          </section>

          <div
            className={`mt-8 grid items-start gap-6 ${isAdmin ? "xl:grid-cols-[minmax(0,1fr)_320px]" : "lg:grid-cols-[minmax(0,1fr)_320px]"}`}
          >
            <section
              aria-labelledby={isAdmin ? "clinics-title" : "clinic-title"}
              className="min-w-0"
              id={isAdmin ? "clinics" : "clinic"}
            >
              <div className="mb-4 flex items-end justify-between gap-4">
                <div>
                  <h2
                    className="text-lg font-semibold tracking-tight text-slate-900"
                    id={isAdmin ? "clinics-title" : "clinic-title"}
                  >
                    {isAdmin ? "Clinic directory" : "Clinic details"}
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    {isAdmin
                      ? "A current view of all registered clinics."
                      : "Your clinic information at a glance."}
                  </p>
                </div>
                {isAdmin && clinics ? (
                  <span className="shrink-0 text-xs font-medium text-slate-400">
                    {clinics.length} {clinics.length === 1 ? "clinic" : "clinics"}
                  </span>
                ) : null}
              </div>

              {isLoading ? (
                <div
                  className="flex min-h-56 items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-500 shadow-sm"
                  aria-live="polite"
                >
                  Loading clinic information…
                </div>
              ) : loadError ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                  <span className="mx-auto flex size-11 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                    <Icon name="building" />
                  </span>
                  <p className="mt-4 text-sm font-medium text-slate-800">
                    Clinic information is unavailable
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    Check your connection and reload the page to try again.
                  </p>
                </div>
              ) : isAdmin ? (
                clinics?.length ? (
                  <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-200/40">
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[680px] text-left">
                        <thead className="border-b border-slate-100 bg-slate-50/80">
                          <tr className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                            <th className="px-5 py-3.5">Clinic</th>
                            <th className="px-5 py-3.5">Status</th>
                            <th className="px-5 py-3.5">Timezone</th>
                            <th className="px-5 py-3.5">Currency</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {clinics.map((item) => (
                            <tr
                              className="transition hover:bg-slate-50/70"
                              key={item.id}
                            >
                              <td className="px-5 py-4">
                                <p className="font-medium text-slate-900">
                                  {item.name}
                                </p>
                                <p className="mt-1 text-xs text-slate-500">
                                  {item.slug}
                                </p>
                              </td>
                              <td className="px-5 py-4">
                                <ClinicStatusBadge status={item.status} />
                              </td>
                              <td className="px-5 py-4 text-sm text-slate-600">
                                {item.timezone}
                              </td>
                              <td className="px-5 py-4 text-sm text-slate-600">
                                {item.currency}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
                    <span className="mx-auto flex size-11 items-center justify-center rounded-full bg-blue-50 text-blue-700">
                      <Icon name="building" />
                    </span>
                    <p className="mt-4 text-sm font-semibold text-slate-900">
                      No clinics yet
                    </p>
                    <p className="mt-1 text-sm text-slate-500">
                      Clinics will appear here once they have been registered.
                    </p>
                  </div>
                )
              ) : clinic ? (
                <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/40">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <span className="flex size-11 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                        <Icon name="building" />
                      </span>
                      <div>
                        <h3 className="font-semibold text-slate-900">
                          {clinic.name}
                        </h3>
                        <p className="mt-1 text-sm text-slate-500">
                          {clinic.slug}
                        </p>
                      </div>
                    </div>
                    <ClinicStatusBadge status={clinic.status} />
                  </div>
                  <dl className="mt-5 grid gap-4 border-t border-slate-100 pt-4 sm:grid-cols-2">
                    <div>
                      <dt className="text-xs font-medium text-slate-400">
                        Timezone
                      </dt>
                      <dd className="mt-1 text-sm font-medium text-slate-700">
                        {clinic.timezone}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-slate-400">
                        Currency
                      </dt>
                      <dd className="mt-1 text-sm font-medium text-slate-700">
                        {clinic.currency}
                      </dd>
                    </div>
                  </dl>
                </article>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center shadow-sm">
                  <p className="text-sm font-medium text-slate-800">
                    No clinic is assigned to this account.
                  </p>
                </div>
              )}
            </section>

            <section
              aria-labelledby="account-title"
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40 sm:p-6"
              id="account"
            >
              <div className="flex items-center gap-3">
                <span className="flex size-11 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-800">
                  {user ? getInitials(user.full_name) : "…"}
                </span>
                <div className="min-w-0">
                  <h2
                    className="truncate text-base font-semibold text-slate-900"
                    id="account-title"
                  >
                    {user?.full_name ?? "Account"}
                  </h2>
                  <p className="mt-0.5 truncate text-sm text-slate-500">
                    {user?.email ?? "Loading account…"}
                  </p>
                </div>
              </div>
              <dl className="mt-6 space-y-4 border-t border-slate-100 pt-5">
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-sm text-slate-500">Username</dt>
                  <dd className="truncate text-right text-sm font-medium text-slate-800">
                    {user?.username ?? "—"}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-sm text-slate-500">Role</dt>
                  <dd className="text-right text-sm font-medium capitalize text-slate-800">
                    {user?.role ?? "—"}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-sm text-slate-500">Account status</dt>
                  <dd className="text-right text-sm font-medium capitalize text-slate-800">
                    {user?.status ?? "—"}
                  </dd>
                </div>
              </dl>
              <button
                className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                type="button"
                onClick={logout}
              >
                <Icon name="logout" className="size-4" />
                Sign out
              </button>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
