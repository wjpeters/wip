let csrf = '';
export function setCsrf(value: string) { csrf = value; }
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`/api${path}`, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', ...(body === undefined ? {} : {'X-CSRF-Token': csrf})},
    ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  if (!r.ok) { const error = await r.json().catch(() => ({})); throw new Error(typeof error.detail === 'string' ? error.detail : 'Controleer de invoer. Bedragen gebruiken een punt als decimaalteken.'); }
  return r.json() as Promise<T>;
}
