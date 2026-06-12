let refreshPromise: Promise<string> | null = null;

export async function enqueueRefresh(refreshFn: () => Promise<string>): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshFn().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export function clearRefreshQueue(): void {
  refreshPromise = null;
}
