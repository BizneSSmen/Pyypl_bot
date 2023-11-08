from math import ceil
from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, CallbackQuery, Document, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from Misc.User_text import Buttons_text, Message_text
from Utils import GetCourse, cancel
from params import USD, FEE
import asyncio
import re

deriveCard: Router = Router()


class DeriveCardStates(StatesGroup):
    phoneNumber: State = State()
    bank: State = State()
    cardNumber: State = State()
    amount: State = State()
    paid: State = State()
    cheque: State = State()


@deriveCard.callback_query(F.data == Buttons_text.derive.Derive.card.value)
async def _deriveCard(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
        [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.sharePhoneNumber, request_contact=True),
          KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
    keyboard.adjust(1)

    mainMsg: Message = await callback.message.answer(text=Message_text.derive.DeriveCard.phoneNumber,
                                                     reply_markup=keyboard.as_markup(resize_keyboard=True))
    data: dict = {"mainMsg": mainMsg.message_id}

    await state.set_state(DeriveCardStates.phoneNumber)
    await state.set_data(data)


@deriveCard.message(DeriveCardStates.phoneNumber)
async def _phoneNumber(message: Message, state: FSMContext, bot: Bot):
    phone: str | None = None
    data: dict = await state.get_data()  # <- GET DATA

    await message.delete()

    if message.contact is not None:
        phone = message.contact.phone_number
    elif message.text is not None:
        phonePattern: re.Pattern = re.compile(r"(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
        phone = phonePattern.match(message.text).group() if phonePattern.match(message.text) else None

    if phone:

        data["phoneNumber"]: str = phone

        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])
        await message.answer(text="Способ вывода: Карта",
                             reply_markup=keyboard.as_markup(resize_keyboard=True))

        inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
            [[InlineKeyboardButton(text=btnTxt.value, callback_data=f"{btnTxt.value}_bank") for btnTxt in
              Buttons_text.derive.DeriveCard]])
        inlineKeyboard.adjust(2)
        mainMsg: Message = await message.answer(text=Message_text.derive.DeriveCard.bank,
                                                reply_markup=inlineKeyboard.as_markup())
        data["mainMsg"]: str = mainMsg.message_id

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(DeriveCardStates.bank)

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.phoneNumberError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@deriveCard.callback_query(F.data.split("_")[-1] == "bank", DeriveCardStates.bank)
async def _cardNumber(callback: CallbackQuery, state: FSMContext):
    data: dict = await state.get_data()
    data["bank"]: str = callback.data.split("_")[0]

    await callback.message.delete()

    mainMsg: Message = await callback.message.answer(
        text=Message_text.derive.DeriveCard.cardNumber.format(__BANK__=data['bank'], __PHONE__=data["phoneNumber"]))
    data['mainMsg']: str = mainMsg.message_id

    await state.set_state(DeriveCardStates.cardNumber)
    await state.set_data(data=data)  # -> SET DATA


@deriveCard.message(DeriveCardStates.cardNumber)
async def _amount(message: Message, state: FSMContext, bot: Bot):
    cardNumber: str | None = None
    data: dict = await state.get_data()  # <- GET DATA

    await message.delete()

    if message.text is not None:
        cardPattern: re.Pattern = re.compile('[0-9]{16}$')
        cardNumber = cardPattern.match(message.text).group() if cardPattern.match(message.text) else None

    if cardNumber:

        data["cardNumber"]: str = " ".join(re.findall('.{%s}' % 4, cardNumber))

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        mainMsg: Message = await message.answer(text=Message_text.derive.DeriveCard.amount.format(__BANK__=data["bank"],
                                                                                                  __CARD__=data[
                                                                                                  "cardNumber"],
                                                                                                  __PHONE__=data[
                                                                                                  "phoneNumber"]))
        data["mainMsg"] = mainMsg.message_id

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(DeriveCardStates.amount)

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.derive.DeriveCard.cardError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@deriveCard.message(DeriveCardStates.amount)
async def _accept(message: Message, state: FSMContext, bot: Bot):
    await message.delete()

    data: dict = await state.get_data()  # <- GET DATA

    if message.text is not None:
        data["usdCourse"]: float = await GetCourse(*USD)() - FEE
        amount = int(message.text) if message.text.isdigit() else 0

        if 5000 <= amount * data["usdCourse"] <= 300_000:

            data["amountUSD"]: str = amount
            data["amountRUB"]: str = str(amount * data["usdCourse"])

            await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

            mainMsg: Message = await message.answer(
                text=Message_text.derive.DeriveCard.result.format(__PHONE__=data["phoneNumber"],
                                                                  __CARD__=data["cardNumber"],
                                                                  __AMOUNT__=data["amountRUB"],
                                                                  __AMOUNT_USD__=data["amountUSD"],
                                                                  __COURSE__=data["usdCourse"], __BANK__=data["bank"]),
                reply_markup=InlineKeyboardBuilder(
                    [[InlineKeyboardButton(text="Подтвердить", callback_data="accept")]]).as_markup())

            data["mainMsg"] = mainMsg.message_id

            cancelOrder: asyncio.Task = asyncio.create_task(cancel(bot, data["mainMsg"], message.chat.id, state))
            data["cancelTask"]: asyncio.Task = cancelOrder

            if "errMsg" in data:
                await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
                del data["errMsg"]

            await state.set_state(DeriveCardStates.paid)
            await state.set_data(data=data)  # -> SET DATA
            await cancelOrder  # >< Start cancelling bid

        elif "errMsg" not in data:
            errorMessage: Message = await message.answer(
                text=Message_text.derive.DeriveCard.amountError.format(__ERR_AMOUNT__=int(amount) * data["usdCourse"]))
            data["errMsg"]: str = errorMessage.message_id
        else:
            try:
                await bot.edit_message_text(chat_id=message.chat.id, message_id=data["errMsg"],
                                            text=Message_text.derive.DeriveCard.amountError.format(
                                                __ERR_AMOUNT__=int(amount) * data["usdCourse"]))
            except TelegramBadRequest:
                pass

    elif "errMsg" not in data:
        errorMessage: Message = await message.answer(
            text=Message_text.derive.DeriveCard.amountError.format(__ERR_AMOUNT__=0))
        data["errMsg"]: str = errorMessage.message_id
    else:
        try:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=data["errMsg"],
                                        text=Message_text.derive.DeriveCard.amountError.format(__ERR_AMOUNT__=0))
        except TelegramBadRequest:
            pass

    await state.set_data(data=data)  # -> SET DATA


@deriveCard.callback_query(F.data == "accept", DeriveCardStates.paid)
async def _payment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()

    await bot.edit_message_text(reply_markup=None, message_id=data["mainMsg"], chat_id=callback.message.chat.id,
                                text=Message_text.derive.DeriveCard.application.format(__PHONE__=data["phoneNumber"],
                                                                                       __CARD__=data["cardNumber"],
                                                                                       __AMOUNT__=data["amountRUB"],
                                                                                       __AMOUNT_USD__=data["amountUSD"],
                                                                                       __COURSE__=data["usdCourse"],
                                                                                       __BANK__=data["bank"],
                                                                                       __BID_NUMBER__=5))

    await callback.message.answer(text=Message_text.derive.DeriveCard.instruction, reply_markup=InlineKeyboardBuilder(
            [[InlineKeyboardButton(text="Оплачено", callback_data="paid")]]).as_markup())


@deriveCard.callback_query(F.data == "paid", DeriveCardStates.paid)
async def _paid(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(text=Message_text.service_text.UserMessageText.cheque)

    await state.set_state(DeriveCardStates.cheque)


@deriveCard.message(DeriveCardStates.cheque)
async def _cheque(message: Message, state: FSMContext, bot: Bot):
    cheque: list | Document | None = next((_ for _ in [message.photo, message.document] if _ is not None), None)

    if cheque:

        data: dict = await state.get_data()  # <- GET DATA

        data["cancelTask"].cancel()

        await state.clear()

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btnTxt.value) for btnTxt in list(Buttons_text.main_menu.MainMenu)[:2]]] +
                     [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[2].value)]] +
                     [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[3].value)]],
            resize_keyboard=True)
        await message.answer(text=Message_text.service_text.UserMessageText.endOfBid,
                             reply_markup=keyboard)

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

    else:
        await message.delete()
        data: dict = await state.get_data()  # <- GET DATA
        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.service_text.UserMessageText.chequeError)
            data["errMsg"]: str = errorMessage.message_id

            await state.set_data(data=data)  # -> SET DATA
