from dataclasses import dataclass


@dataclass
class ChashExchange:
    keyboardChangeMsg: str = "🔄 Обмен наличных"
    phoneNumber: str = "Введите номер телефона, на который зарегистрирован ваш Pyypl аккаунт:"
    wallet: str = "Выберите валюту для обмена:"
    amount: str = "Введите сумму обмена:"
    amountError: str = "Недопустимая сумма для обмена.\nПовторите попытку."
    result: str = \
'''
<b>Подтвердите данные заявки:</b>

Способ обмена: Наличными
Номер телефона: {__PHONE__}
Валюта обмена: {__WALLET__} 
Сумма обмена: {__AMOUNT__}

Истекает: {__END__DATE__} UTC <i>(через 20 минут)</i>
'''
    application: str = \
'''
<b>Спасибо! Заявка сформирована::</b>

Способ обмена: Наличными
Номер телефона: {__PHONE__}
Валюта обмена: {__WALLET__} 
Сумма обмена: {__AMOUNT__}

Истекает: {__END__DATE__} UTC <i>(через 2 дня)</i>
'''
