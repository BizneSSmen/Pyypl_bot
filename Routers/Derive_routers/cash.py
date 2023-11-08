import time

from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, CallbackQuery, Document, ReplyKeyboardMarkup, \
    File
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiomysql import Pool

from DataBase import Database
from Entities import Claim
from Misc.User_text import Buttons_text, Message_text
from Utils import GetCourse, cancel
from params import USD, FEE
import asyncio
import re

deriveCash: Router = Router()


class DeriveCashStates(StatesGroup):
    phoneNumber: State = State()
    amount: State = State()
    paid: State = State()
    cheque: State = State()


@deriveCash.callback_query(F.data == Buttons_text.derive.Derive.cash.value)
async def _deriveCard(callback: CallbackQuery, state: FSMContext):
    claim: Claim = Claim()
    claim.setCredit()
    claim.setCurrencyA('USD')
    claim.setCurrencyB('RUB')
    data: dict[str, Claim] = {'claim': claim}

    await callback.message.delete()

    keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
        [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.sharePhoneNumber, request_contact=True),
          KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
    keyboard.adjust(1)

    mainMsg: Message = await callback.message.answer(text=Message_text.derive.DeriveCash.phoneNumber,
                                                     reply_markup=keyboard.as_markup(resize_keyboard=True))
    data["mainMsg"] = mainMsg.message_id

    await state.set_state(DeriveCashStates.phoneNumber)
    await state.set_data(data)  # -> SET DATA


@deriveCash.message(DeriveCashStates.phoneNumber)
async def _phoneNumber(message: Message, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    await message.delete()

    if message.contact is not None:
        claim.setPhoneNumber(message.contact.phone_number)
    elif message.text is not None:
        claim.setPhoneNumber(message.text)

    if claim.phoneNumber:

        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])
        await message.answer(text="Способ вывода: Наличными (Москва)",
                             reply_markup=keyboard.as_markup(resize_keyboard=True))

        mainMsg: Message = await message.answer(text=Message_text.derive.DeriveCash.amount)
        data["mainMsg"]: str = mainMsg.message_id
        data['claim'] = claim

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(DeriveCashStates.amount)

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.phoneNumberError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@deriveCash.message(DeriveCashStates.amount)
async def _accept(message: Message, state: FSMContext, bot: Bot, pool: Pool):
    data = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    await message.delete()

    if message.text is not None:
        claim.setExchangeAppliedRate(await GetCourse(*USD)())
        claim.setFee(FEE)
        claim.setTargetAmount(amount=message.text)
        claim.setFinalAmount(claim.targetAmount * (claim.exchangeAppliedRate + claim.fee))

        if 5000 <= claim.finalAmount <= 300_000:

            description: str = Message_text.derive.DeriveCash.result.format(__PHONE__=claim.phoneNumber,
                                                                            __AMOUNT_USD__=claim.targetAmount,
                                                                            __TIME_LEFT__=20)
            claim.setDescription(description)
            claim.setCreated()
            data['timeLeft'] = int(time.time()) + 1200

            bd: Database = Database(pool)
            claimId: str = await bd.insertСlaim(claim.getAllAttr())
            data["claimId"]: str = claimId

            await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

            mainMsg: Message = await message.answer(
                text=description,
                reply_markup=InlineKeyboardBuilder(
                    [[InlineKeyboardButton(text="Подтвердить", callback_data="done")]]).as_markup())

            cancelOrder: asyncio.Task = asyncio.create_task(cancel(bot, data["mainMsg"], message.chat.id, state))
            data["cancelTask"]: asyncio.Task = cancelOrder
            data["mainMsg"] = mainMsg.message_id
            data['claim'] = claim

            if "errMsg" in data:
                await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
                del data["errMsg"]

            await state.set_state(DeriveCashStates.paid)
            await state.set_data(data=data)  # -> SET DATA
            await cancelOrder  # >< Start cancelling bid

        elif "errMsg" not in data:
            errorMessage: Message = await message.answer(
                text=Message_text.derive.DeriveCard.amountError.format(__ERR_AMOUNT__=claim.finalAmount))
            data["errMsg"]: str = errorMessage.message_id
        else:
            try:
                await bot.edit_message_text(chat_id=message.chat.id, message_id=data["errMsg"],
                                            text=Message_text.derive.DeriveCard.amountError.format(
                                                __ERR_AMOUNT__=claim.finalAmount))
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


@deriveCash.callback_query(F.data == "done", DeriveCashStates.paid)
async def _payment(callback: CallbackQuery, state: FSMContext, bot: Bot, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setApproved()
    data['claim'] = claim
    data["cancelTask"].cancel()

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await bot.edit_message_text(reply_markup=None, message_id=data["mainMsg"], chat_id=callback.message.chat.id,
                                text=Message_text.derive.DeriveCash.application.format(__PHONE__=claim.phoneNumber,
                                                                                       __AMOUNT_USD__=claim.targetAmount,
                                                                                       __BID_NUMBER__=data['claimId']))

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btnTxt.value) for btnTxt in list(Buttons_text.main_menu.MainMenu)[:2]]] +
                 [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[2].value)]] +
                 [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[3].value)]],
        resize_keyboard=True)
    await callback.message.answer(text=Message_text.service_text.UserMessageText.endOfBid,
                                  reply_markup=keyboard)

    await state.clear()

