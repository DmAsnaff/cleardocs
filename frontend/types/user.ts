export type UserRole = "user" | "admin" | "moderator";

export interface User {
  id: string;
  email: string;
  full_name: string;
  preferred_language: string;
  role: UserRole;
  is_verified: boolean;
  created_at: string;
}

export interface AuthTokens {
  access: string;
}

export interface ApiResponse<T = null> {
  status: "success" | "error";
  message: string;
  data: T;
  errors?: Record<string, string[]>;
}
