import { apiRequest } from "./client";
import type {
    TokenPair,
    RegisterRequest,
    LoginRequest,
    GuestLoginRequest,
    UpgradeGuestRequest,
} from "../types/auth"

export function register(body: RegisterRequest): Promise<TokenPair> {
    return apiRequest<TokenPair>("/auth/register", { method: "POST", body });
}

export function login(body: LoginRequest): Promise<TokenPair> {
    return apiRequest<TokenPair>("/auth/login", { method: "POST", body });
}

export function loginAsGuest(body: GuestLoginRequest): Promise<TokenPair> {
    return apiRequest<TokenPair>("/auth/guest", { method: "POST", body });
}

export function upgradeGuest(body: UpgradeGuestRequest, token: string): Promise<TokenPair> {
    return apiRequest<TokenPair>("/auth/upgrade", { method: "POST", body, token });
}

export function refresh(refreshToken: string): Promise<TokenPair> {
  return apiRequest<TokenPair>("/auth/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });
}