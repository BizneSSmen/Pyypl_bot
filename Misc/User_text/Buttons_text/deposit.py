from enum import Enum


class Deposit(Enum):
    # money: str = "Наличными"
    card: str = "💳 Картой"
    # crypto: str = "Крипто"
    sbp: str = "🔄 СБП"
    course: str = "📊 Текущий курс "
    

class DepositCard(Enum):
    bank1: str = "Сбер 🟢"
    bank2: str = "Тинькофф 🟡"
    

class DepositSBP(Enum):
    wallet1: str = "RUB"