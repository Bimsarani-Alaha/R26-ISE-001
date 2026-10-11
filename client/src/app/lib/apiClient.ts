const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export async function requestJson<T>(
  path: string,
  payload?: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...(payload === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail = error?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: { msg: string }) => item.msg).join("; ")
          : `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}
