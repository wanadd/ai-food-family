export function getTelegramBotUsername(): string | null {
  const username = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME?.trim();
  return username || null;
}

export function getTelegramAppShortName(): string | null {
  const shortName = process.env.NEXT_PUBLIC_TELEGRAM_APP_SHORT_NAME?.trim();
  return shortName || null;
}

export function buildMiniAppUrl(): string | null {
  const username = getTelegramBotUsername();
  if (!username) {
    return null;
  }

  const shortName = getTelegramAppShortName();
  if (shortName) {
    return `https://t.me/${username}/${shortName}`;
  }

  return `https://t.me/${username}?startapp`;
}
