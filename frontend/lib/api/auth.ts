import { apiRequest } from "./client";

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  must_change_password: boolean;
};

export type CurrentUser = {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: "admin" | "dental";
  status: "active" | "disabled";
  must_change_password: boolean;
  created_at: string;
};

export function login(payload: LoginPayload): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser(): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/auth/me");
}
