import { apiRequest } from "./client";

export type Clinic = {
  id: string;
  name: string;
  slug: string;
  registration_number: string | null;
  website: string | null;
  description: string | null;
  timezone: string;
  currency: string;
  status: "draft" | "pending_verification" | "active" | "suspended" | "closed";
};

export type CreateClinicPayload = {
  name: string;
  owner_username: string;
  owner_email: string;
  owner_full_name: string;
  timezone?: string;
  currency?: string;
  owner_password: string;
  owner_password_confirmation: string;
};

export type UpdateClinicPayload = Partial<
  Pick<
    Clinic,
    "name" | "registration_number" | "website" | "description" | "timezone" | "currency"
  >
>;

export function listClinics(): Promise<Clinic[]> {
  return apiRequest<Clinic[]>("/admin/clinics");
}

export function createClinic(payload: CreateClinicPayload): Promise<Clinic> {
  return apiRequest<Clinic>("/admin/clinics", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMyClinic(): Promise<Clinic> {
  return apiRequest<Clinic>("/clinic/me");
}

export function updateMyClinic(payload: UpdateClinicPayload): Promise<Clinic> {
  return apiRequest<Clinic>("/clinic/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
