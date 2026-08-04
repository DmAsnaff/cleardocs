import apiClient from "./client";
import type { ApiResponse, User, AuthTokens } from "@/types/user";

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  preferred_language?: string;
}

export interface PasswordResetPayload {
  email: string;
}

export interface PasswordResetConfirmPayload {
  token: string;
  password: string;
  password_confirm: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

export const authApi = {
  register(payload: RegisterPayload) {
    return apiClient.post<ApiResponse<User>>("/auth/register/", payload);
  },

  login(payload: LoginPayload) {
    return apiClient.post<ApiResponse<AuthTokens>>("/auth/login/", payload);
  },

  logout() {
    return apiClient.post<ApiResponse>("/auth/logout/");
  },

  refreshToken() {
    return apiClient.post<ApiResponse<AuthTokens>>("/auth/token/refresh/");
  },

  verifyEmail(token: string) {
    return apiClient.post<ApiResponse>("/auth/verify-email/", { token });
  },

  requestPasswordReset(payload: PasswordResetPayload) {
    return apiClient.post<ApiResponse>("/auth/password-reset/", payload);
  },

  confirmPasswordReset(payload: PasswordResetConfirmPayload) {
    return apiClient.post<ApiResponse>("/auth/password-reset/confirm/", payload);
  },

  getProfile() {
    return apiClient.get<ApiResponse<User>>("/auth/me/");
  },

  updateProfile(payload: ProfileUpdatePayload) {
    return apiClient.patch<ApiResponse<User>>("/auth/me/", payload);
  },

  deleteAccount() {
    return apiClient.delete<ApiResponse>("/auth/me/");
  },

  changePassword(payload: ChangePasswordPayload) {
    return apiClient.post<ApiResponse>("/auth/me/change-password/", payload);
  },

  dataExport() {
    return apiClient.get("/auth/me/data-export/", { responseType: "blob" });
  },
};
