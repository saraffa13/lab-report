import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

export default function HealthPage() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await apiClient.get("/health/")).data,
  });

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">API Health</h1>
      {isLoading && <p className="text-muted-foreground">Checking…</p>}
      {error && <p className="text-destructive">API unreachable.</p>}
      {data && (
        <pre className="rounded border bg-muted p-4 text-sm">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
