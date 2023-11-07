from dataclasses import dataclass


@dataclass
class UserMessageText:
    helloTxt: str =\
'''
Привет, {__NAME__}!
Добро пожаловать в Pyypl Bot, который умеет пополнять и подключать пластиковые карты к Вашему аккаунту в банке Pyypl.

Очень важно❗️
Заказать или подключить карту резидентам Дубая или с Дубайским номером телефона нельзя.

Оформление и пополнение происходит в порядке очереди.
'''
    cancel: str = "Отменено"
    FAQ: str = \
'''
<a href='https://telegra.ph/PYYPL---chto-ehto-takoe-05-21'>PYYPL - что это такое?</a>
<a href='https://telegra.ph/Kak-popolnit-schet-Pyypl-cherez-Telegram-bota-08-15'>Как пополнить счет Pyypl через Telegram бота</a>
<a href='https://telegra.ph/Kak-vyvesti-sredstva-so-scheta-Pyypl-cherez-Telegram-bota-09-12
'>Как вывести средства со счета Pyypl через Telegram бота</a>
<a href='https://telegra.ph/Kak-popolnit-PYYPL-so-scheta-QIWI-05-21
'>Как пополнить PYYPL с QIWI</a>
<a href='https://telegra.ph/Kak-zakazat-plastikovuyu-kartu-Pyypl-01-13
'>Как заказать пластиковую карту PYYPL</a>
<a href='https://telegra.ph/Kak-podklyuchit-plastikovuyu-kartu-v-PYYPL-01-13
'>Как подключить пластиковую карту в PYYPL</a>
<a href='https://telegra.ph/Kak-uvelichit-limit-svoego-akkaunta-PYYPL-06-29
'>Как увеличить лимит своего аккаунта PYYPL</a>
<a href='https://telegra.ph/Kak-popolnit-koshelek-Binance-dlya-perevoda-na-kartu-Pyypl-01-08
'>Как пополнить кошелек Binance для перевода на карту PYYPL</a>
<a href='https://telegra.ph/Popolnenie-cherez-obmenniki-BestChange-na-Binance-dlya-perevoda-kartu-Pyypl-01-08
'>Как пополнить карту PYYPL через обменники BestChange</a>
<a href='https://telegra.ph/Kak-popolnit-kartu-PYYPL-s-koshelka-MetaMask-01-08
'>Как пополнить карту PYYPL с кошелька MetaMask</a>
<a href='https://telegra.ph/Kak-popolnit-kartu-PYYPL-s-koshelka-Trust-Wallet-01-08
'>Как пополнить карту PYYPL с кошелька Trust Wallet</a>
<a href='https://telegra.ph/Kak-sdelat-mezhdunarodnyj-perevod-s-PYYPL-06-29
'>Как сделать международный перевод с PYYPL</a>
<a href='https://telegra.ph/Pyypl-Russia-FAQ-01-08
'>FAQ: Ответы на вопросы</a>
<a href='https://telegra.ph/Tarify-karty-PYYPL-01-08
'>Тарифы PYYPL</a>
<a href='https://telegra.ph/PayPal-i-privyazka-karty-PYYPL-05-21
'>Привязка карты PYYPL к PayPal</a>
<a href='https://telegra.ph/Magaziny-s-podtverzhdennoj-oplatoj-PYYPL-07-20'>Магазины с подтвержденной оплатой PYYPL</a>

Официальный канал Pyypl Russian Community:
@pyypl_ru

Официальный телеграм бот службы поддержки: @ru_pyypl_support_bot 

Остались вопросы?
Напишите нам в поддержку внутри самого приложения, для более быстрого решения вопроса.

ОСТЕРЕГАЙТЕСЬ МОШЕННИКОВ! МЫ НЕ ПИШЕМ ПЕРВЫЕ!
'''
    cancelOrder: str = "Заявка отменена"
    cheque: str = "‼️ 📃 Пожалуйста, отправьте чек по операции (должно быть указано ФИО отправителя) в этот чат"
    chequeError: str = "В сообщении отсуствует чек по опреации, повторите попытку"
    endOfBid: str = "✔️ Спасибо! Проверяем Вашу заявку..."
    endOfLongBid: str = "✔️ Ожидайте, с Вами свяжется менеджер, и согласует дальнейшие действия."
