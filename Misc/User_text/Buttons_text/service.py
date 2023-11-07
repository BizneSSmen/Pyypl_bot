from dataclasses import dataclass


@dataclass
class ServiceButtonText:
    cancel: str = "❌ Отменить"
    sharePhoneNumber: str = "Поделиться номером телефона"