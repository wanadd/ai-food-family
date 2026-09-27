from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class PlatformType(StrEnum):
    TELEGRAM = "telegram"
    WEB = "web"
    MAX = "max"
    ANDROID = "android"
    IOS = "ios"


class PlatformCapability(StrEnum):
    AUTH_BOOTSTRAP = "auth_bootstrap"
    VIEWPORT = "viewport"
    SAFE_AREA = "safe_area"
    FULLSCREEN = "fullscreen"
    BACK = "back"
    THEME = "theme"
    HAPTICS = "haptics"
    SHARE = "share"
    DEEP_LINK = "deep_link"
    CAMERA = "camera"
    FILE_PICKER = "file_picker"
    NOTIFICATIONS = "notifications"
    PUSH = "push"
    PAYMENTS = "payments"
    EXTERNAL_BROWSER = "external_browser"


@dataclass(frozen=True)
class PlatformCapabilities:
    client_type: PlatformType
    values: frozenset[PlatformCapability]

    def supports(self, capability: PlatformCapability) -> bool:
        return capability in self.values


class PlatformAdapter(Protocol):
    client_type: PlatformType

    def capabilities(self) -> PlatformCapabilities:
        ...


@dataclass(frozen=True)
class TelegramPlatformAdapter:
    client_type: PlatformType = PlatformType.TELEGRAM

    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            self.client_type,
            frozenset(
                {
                    PlatformCapability.AUTH_BOOTSTRAP,
                    PlatformCapability.VIEWPORT,
                    PlatformCapability.SAFE_AREA,
                    PlatformCapability.FULLSCREEN,
                    PlatformCapability.BACK,
                    PlatformCapability.THEME,
                    PlatformCapability.SHARE,
                    PlatformCapability.DEEP_LINK,
                    PlatformCapability.FILE_PICKER,
                    PlatformCapability.NOTIFICATIONS,
                    PlatformCapability.EXTERNAL_BROWSER,
                }
            ),
        )


@dataclass(frozen=True)
class WebPlatformAdapter:
    client_type: PlatformType = PlatformType.WEB

    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            self.client_type,
            frozenset(
                {
                    PlatformCapability.VIEWPORT,
                    PlatformCapability.SAFE_AREA,
                    PlatformCapability.BACK,
                    PlatformCapability.THEME,
                    PlatformCapability.SHARE,
                    PlatformCapability.DEEP_LINK,
                    PlatformCapability.FILE_PICKER,
                    PlatformCapability.EXTERNAL_BROWSER,
                }
            ),
        )
