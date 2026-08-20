// Обёртка над fetch

// URL backend'а
const BASE_URL = "http://localhost:8000/api/v1";

// Простой класс ошибки
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}
interface RequestOptions {
    method?: "GET" | "POST" | "PATCH" | "DELETE";
    body?: unknown;
    token?: string; // access-токен, если запрос требует авторизации
}

export async function apiRequest<TResponse>(
    path: string,
    options: RequestOptions = {},
): Promise<TResponse> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json"
    };
    if (options.token) {
        headers["Authorization"] = `Bearer ${options.token}`;
    }

    const response = await fetch(`${BASE_URL}${path}`, {
        method: options.method ?? "GET",
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined
    });

    // 204 No Content (например DELETE)
    if (response.status === 204) {
        return undefined as TResponse
    }

    const data = await response.json()
    if (!response.ok) {
        throw new ApiError(response.status, data.detail ?? "Unknown error");
    }

    return data as TResponse
}