// Хранит токены текущего залогиненого пользователя на уровне всего приложения

import { createContext, useContext, useState, type ReactNode } from "react";
import type { TokenPair } from "../types/auth"

interface AuthContextValue {
    tokens: TokenPair | null;
    setTokens: (tokens: TokenPair | null) => void;
}

// createContext создаёт контейнер для расшаривания данных
const AuthContext = createContext<AuthContextValue | null>(null)

// компонент обёртка. всё, что положено внутрь <AuthProvider>...</AuthProvider>
// получает доступ к tokens/setTokens через useAuth()
export function AuthProvider({ children }: { children: ReactNode }) {
    const [tokens, setTokens] = useState<TokenPair | null>(null);

    return (
        <AuthContext.Provider value={{ tokens, setTokens }}>
            {children}
        </AuthContext.Provider>
    );
}

// Хук для чтения контекста из любого компонента
export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext);
    if (context === null) {
        // сработает, если кто-то запустит useAuth вне AuthProvider
        throw new Error("useAuth must be used within AuthProvider")
    }
    return context;
}