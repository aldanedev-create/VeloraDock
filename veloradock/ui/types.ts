export interface Result {
  id: string;
  title: string;
  subtitle: string;
  kind: string;
  value: string;
  confirm: boolean;
}
export interface SearchResponse { items: Result[]; elapsed_ms: number; }
export interface NativeReply { error?: string; message?: string; }
