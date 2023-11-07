from enum import Enum


class Derive(Enum):
    card: str = "💳 Карта"
    cash: str = "💸 Наличными (Москве)"
    course: str = "📊 Текущий курс"


class DeriveCard(Enum):
    bank1: str = "Сбер 🟢"
    bank2: str = "Тинькофф 🟡"