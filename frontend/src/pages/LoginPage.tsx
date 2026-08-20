// Форма входа: email + пароль -> POST /auth/login -> сохраняем токены в AuthContext

import { useState, type FormEvent } from "react";
import { useAuth } from "../context/AuthContext"
import { ApiError } from "../api/client";
import { login } from "../api/auth"

export function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const { setTokens } = useAuth();

    // Вызывается при отпрвке формы (нажатии Enter или кнопки Submit)
    async function handleSubmit(event: FormEvent) {
        event.preventDefault();

        setError(null);
        setIsSubmitting(true);

        try {
            const tokens = await login({ email, password })
            setTokens(tokens);
        } catch (err) {
            if (err instanceof ApiError) {
                setError(err.detail);
            } else {
                setError("Something went wrong");
            }
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form onSubmit={handleSubmit}>
            <h1>Login</h1>

            <div>
                <label htmlFor="email">Email</label>
                <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
            </div>

            <div>
                <label htmlFor="password">Password</label>
                <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
            </div>

            {error && <p style={{ color: "red" }}>{error}</p>}

            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Logging in ..." : "Login"}
            </button>
        </form>
    );
}