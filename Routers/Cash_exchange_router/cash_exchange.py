import asyncio
import re
import time

from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import KeyboardButton, Message, InlineKeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiomysql import Pool

from DataBase import Database
from Entities import Claim
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
    claim: Claim = Claim()
    claim.setChange()

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
    data: dict[str, Claim] = {'claim': claim, "mainMsg": mainMsg.message_id}

    await state.set_state(CashExchangeStates.phoneNumber)
    await state.set_data(data)  # -> SET DATA


@cashExchange.message(CashExchangeStates.phoneNumber)
async def _wallet(message: Message, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    await message.delete()

    if message.contact is not None:
        claim.setPhoneNumber(message.contact.phone_number)
    elif message.text is not None:
        claim.setPhoneNumber(message.text)

    if claim.phoneNumber:

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
            [[InlineKeyboardButton(text=btnTxt.value, callback_data=f"{btnTxt.value}_wallet") for btnTxt in
              Buttons_text.cash_exchange.CashExchange]])
        inlineKeyboard.adjust(1)
        mainMsg: Message = await message.answer(text=Message_text.cash_exchange.ChashExchange.wallet,
                                                reply_markup=inlineKeyboard.as_markup())

        data["mainMsg"]: str = mainMsg.message_id
        data['claim'] = claim

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
    claim: Claim = data['claim']
    claim.setCurrencyA(callback.data.split("_")[0])
    claim.setCurrencyB(claim.currencyA)

    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["mainMsg"])

    keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
        [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
    mainMsg: Message = await callback.message.answer(text=Message_text.cash_exchange.ChashExchange.amount,
                                                     reply_markup=keyboard.as_markup(resize_keyboard=True))
    data["mainMsg"]: str = mainMsg.message_id
    data['claim'] = claim

    await state.set_state(CashExchangeStates.amount)
    await state.set_data(data=data)  # -> SET DATA


@cashExchange.message(CashExchangeStates.amount)
async def _amount(message: Message, state: FSMContext, bot: Bot, pool: Pool):
    data = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    await message.delete()

    if message.text is not None:
        claim.setTargetAmount(message.text)
        claim.setFinalAmount(message.text)
        claim.setExchangeAppliedRate(1)
        claim.setFee(0)

    if claim.finalAmount >= 1:
        description: str = Message_text.cash_exchange.ChashExchange.result.format(__WALLET__=claim.currencyA,
                                                                                  __PHONE__=claim.phoneNumber,
                                                                                  __AMOUNT__=claim.finalAmount,
                                                                                  __TIME_LEFT__=20)
        claim.setDescription(description)
        claim.setCreated()
        data['timeLeft'] = int(time.time()) + 1200

        bd: Database = Database(pool)
        claimId: str = await bd.insertСlaim(claim.getAllAttr())
        data["claimId"]: str = claimId

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        await message.answer(text="Спасибо!", reply_markup=keyboard.as_markup(resize_keyboard=True))

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

        await state.set_state(CashExchangeStates.accept)
        await state.set_data(data=data)  # -> SET DATA
        await cancelOrder

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.cash_exchange.ChashExchange.amountError)
            data["errMsg"]: str = errorMessage.message_id

            await state.set_data(data=data)  # -> SET DATA


@cashExchange.callback_query(F.data == "done", CashExchangeStates.accept)
async def _accept(callback: CallbackQuery, state: FSMContext, bot: Bot, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setApproved()
    data['claim'] = claim
    data["cancelTask"].cancel()

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await bot.edit_message_text(
        text=Message_text.cash_exchange.ChashExchange.application.format(__WALLET__=claim.currencyA,
                                                                         __AMOUNT__=claim.targetAmount,
                                                                         __PHONE__=claim.phoneNumber,
                                                                         ), reply_markup=None,
        message_id=data["mainMsg"], chat_id=callback.message.chat.id)

    await state.clear()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btnTxt.value) for btnTxt in list(Buttons_text.main_menu.MainMenu)[:2]]] +
                 [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[2].value)]] +
                 [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[3].value)]],
        resize_keyboard=True)
    await callback.message.answer(text=Message_text.service_text.UserMessageText.endOfLongBid,
                                  reply_markup=keyboard)
