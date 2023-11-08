import asyncio
import re

from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import KeyboardButton, Message, InlineKeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from Misc.User_text import Buttons_text, Message_text
from aiogram.fsm.context import FSMContext

from Utils import GetCourse, cancel
from params import USD, FEE

cashExchange: Router = Router()


class CashExchangeStates(StatesGroup):
    phoneNumber: State = State()
    wallet: State = State()
    amount: State = State()
    accept: State = State()


@cashExchange.message(F.text == Buttons_text.main_menu.MainMenu.deriveAmount.value)
async def _deriveCash(message: Message, state: FSMContext):
    keyboardButton: ReplyKeyboardBuilder = (ReplyKeyboardBuilder().
                                            add(KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)))
    await message.answer(text=Message_text.cash_exchange.ChashExchange.keyboardChangeMsg,
                         reply_markup=keyboardButton.as_markup(resize_keyboard=True))

    keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
        [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.sharePhoneNumber, request_contact=True),
          KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
    keyboard.adjust(1)
    mainMsg: message = await message.answer(text=Message_text.cash_exchange.ChashExchange.phoneNumber,
                                            reply_markup=keyboard.as_markup(resize_keyboard=True))

    data: dict = {"mainMsg": mainMsg.message_id}

    await state.set_state(CashExchangeStates.phoneNumber)
    await state.set_data(data)  # -> SET DATA


@cashExchange.message(CashExchangeStates.phoneNumber)
async def _wallet(message: Message, state: FSMContext, bot: Bot):
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

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
            [[InlineKeyboardButton(text=btnTxt.value, callback_data=f"{btnTxt.value}_wallet") for btnTxt in
              Buttons_text.cash_exchange.CashExchange]])
        inlineKeyboard.adjust(1)
        mainMsg: Message = await message.answer(text=Message_text.cash_exchange.ChashExchange.wallet,
                                                reply_markup=inlineKeyboard.as_markup())

        data["mainMsg"]: str = mainMsg.message_id

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(CashExchangeStates.wallet)

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.phoneNumberError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@cashExchange.callback_query(F.data.split("_")[-1] == "wallet", CashExchangeStates.wallet)
async def _amount(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    data["wallet"] = callback.data.split("_")[0]

    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["mainMsg"])

    keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
        [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
    mainMsg: Message = await callback.message.answer(text=Message_text.cash_exchange.ChashExchange.amount,
                                                     reply_markup=keyboard.as_markup(resize_keyboard=True))
    data["mainMsg"]: str = mainMsg.message_id

    await state.set_state(CashExchangeStates.amount)
    await state.set_data(data=data)  # -> SET DATA


@cashExchange.message(CashExchangeStates.amount)
async def _amount(message: Message, state: FSMContext, bot: Bot):
    amount: int = 0
    data: dict = await state.get_data()  # <- GET DATA

    await message.delete()

    if message.text is not None:
        amount = int(message.text) if message.text.isdigit() else 0

    if amount >= 1:
        data["amount"]: str = amount

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        await message.answer(text="Спасибо!", reply_markup=keyboard.as_markup(resize_keyboard=True))

        mainMsg: Message = await message.answer(
            text=Message_text.cash_exchange.ChashExchange.result.format(__WALLET__=data["wallet"],
                                                                        __PHONE__=data["phoneNumber"],
                                                                        __AMOUNT__=data["amount"],
                                                                        __END__DATE__="temp"),
            reply_markup=InlineKeyboardBuilder(
                [[InlineKeyboardButton(text="Подтвердить", callback_data="accept")]]).as_markup())

        cancelOrder: asyncio.Task = asyncio.create_task(cancel(bot, data["mainMsg"], message.chat.id, state))
        data["cancelTask"]: asyncio.Task = cancelOrder
        data["mainMsg"] = mainMsg.message_id

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(CashExchangeStates.accept)
        await state.set_data(data=data)  # -> SET DATA
        await cancelOrder

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.cash_exchange.ChashExchange.amountError)
            data["errMsg"]: str = errorMessage.message_id

            await state.set_data(data=data)  # -> SET DATA


@cashExchange.callback_query(F.data == "accept", CashExchangeStates.accept)
async def _accept(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA

    await bot.edit_message_text(
        text=Message_text.cash_exchange.ChashExchange.application.format(__WALLET__=data["wallet"],
                                                                         __AMOUNT__=data["amount"],
                                                                         __PHONE__=data["phoneNumber"],
                                                                         __END__DATE__="temp"), reply_markup=None,
        message_id=data["mainMsg"], chat_id=callback.message.chat.id)

    await state.clear()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btnTxt.value) for btnTxt in list(Buttons_text.main_menu.MainMenu)[:2]]] +
                 [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[2].value)]] +
                 [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[3].value)]],
        resize_keyboard=True)
    await callback.message.answer(text=Message_text.service_text.UserMessageText.endOfLongBid,
                                  reply_markup=keyboard)
