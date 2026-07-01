/** Local prod-parity auth gate. Never active in production builds. */

export function isLocalParityHost(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1";
}

export function isLocalParityModeEnabled(): boolean {
  if (typeof process !== "undefined" && process.env.NODE_ENV === "production") {
    return false;
  }
  return (
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE === "true" &&
    isLocalParityHost()
  );
}
