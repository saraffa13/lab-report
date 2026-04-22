// Shared TypeScript types land here as the API surface grows.
export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};
