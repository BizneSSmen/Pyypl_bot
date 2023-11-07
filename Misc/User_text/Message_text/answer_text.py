from datetime import datetime
from enum import Enum


class CardOrder(Enum):
    keyboardChangeMsg: str = "💳 Заказ карты"
    infoTxt: str = \
'''
В данный момент мы можем доставить карту в несколько стран.
Если Вашей страны нет в списке, Вы можете оставить предварительную заявку и мы свяжемся с Вами когда будет возможность доставки в Вашу страну
'''
    cardTxt: str = "Выберите страну доставки:"
