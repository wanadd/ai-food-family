/** IANA timezone from the user's device (for reminder scheduling). */
export function getDeviceTimezone(): string {
  if (typeof Intl === "undefined" || !Intl.DateTimeFormat) {
    return "Europe/Moscow";
  }
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Moscow";
}
