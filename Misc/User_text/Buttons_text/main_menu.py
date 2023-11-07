from enum import Enum


class MainMenu(Enum):
    deposit: str = "💵 Пополнить Pyypl"
    # voucher: str = "🎟️ Купить ваучер" #delete
    # account: str = "💼 Личный кабинет" #delete
    derive: str = "💰 Вывести c Pyypl"
    # card: str = "💳 Заказать карту" #delete
    deriveAmount: str = "🔄 Обмен наличных с зачислением на карту"
    faq: str = "❔ FAQ"