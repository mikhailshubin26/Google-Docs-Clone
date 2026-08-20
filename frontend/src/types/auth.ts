// Описание форм данных TS

export interface TokenPair {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    display_name: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface GuestLoginRequest {
    display_name: string;
}

export interface UpgradeGuestRequest {
    email: string;
    password: string;
}