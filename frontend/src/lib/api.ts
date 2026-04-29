const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function createSession(mode: string) {
  return request<{ session_id: string; chamber_order: string[]; session_flow: unknown[] }>(
    "/sessions",
    { method: "POST", body: JSON.stringify({ mode }) }
  );
}

export async function recordConsent(sessionId: string, consent: boolean) {
  return request("/sessions/consent", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, data_collection: consent }),
  });
}

export async function sendTransition(sessionId: string, event: string, data = {}) {
  return request<Record<string, unknown>>("/sessions/transition", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, event, data }),
  });
}

export async function recordSignals(
  sessionId: string,
  chamberId: string,
  interactionId: string,
  events: Record<string, unknown>[]
) {
  return request<{ features_extracted: number; features: Record<string, number> }>(
    "/signals",
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        chamber_id: chamberId,
        interaction_id: interactionId,
        events,
      }),
    }
  );
}

export async function companionChat(
  sessionId: string,
  chamberId: string,
  message: string,
  history: { role: string; content: string }[] = []
) {
  return request<{ response: string }>("/companion/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      chamber_id: chamberId,
      message,
      history,
    }),
  });
}

export async function computeScores(sessionId: string, signals: Record<string, number>) {
  return request<Record<string, unknown>>("/scoring/compute", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, signals }),
  });
}
