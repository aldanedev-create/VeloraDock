export async function request(path: string, token: string, payload: object = {}): Promise<any> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-velora-token": token },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request failed.");
  return data;
}

export function native(): any {
  return (window as any).pywebview?.api;
}
