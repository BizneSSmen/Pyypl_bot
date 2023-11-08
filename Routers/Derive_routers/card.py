import time
from math import ceil
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

    mainMsg: Message = await callback.message.answer(text=Message_text.derive.DeriveCard.phoneNumber,
                                                     reply_markup=keyboard.as_markup(resize_keyboard=True))
    data["mainMsg"] = mainMsg.message_id

    await state.set_state(DeriveCardStates.phoneNumber)
    await state.set_data(data)  # -> SET DATA


@deriveCard.message(DeriveCardStates.phoneNumber)
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
        await message.answer(text="Способ вывода: Карта",
                             reply_markup=keyboard.as_markup(resize_keyboard=True))

        inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
            [[InlineKeyboardButton(text=btnTxt.value, callback_data=f"{btnTxt.value}_bank") for btnTxt in
              Buttons_text.derive.DeriveCard]])
        inlineKeyboard.adjust(2)
        mainMsg: Message = await message.answer(text=Message_text.derive.DeriveCard.bank,
                                                reply_markup=inlineKeyboard.as_markup())
        data["mainMsg"]: str = mainMsg.message_id
        data['claim'] = claim

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
    data: dict = await state.get_data()  # <- GET DATA
    data["bank"]: str = callback.data.split("_")[0]
    claim: Claim = data['claim']

    await callback.message.delete()

    mainMsg: Message = await callback.message.answer(
        text=Message_text.derive.DeriveCard.cardNumber.format(__BANK__=data['bank'], __PHONE__=claim.phoneNumber))
    data['mainMsg']: str = mainMsg.message_id

    await state.set_state(DeriveCardStates.cardNumber)
    await state.set_data(data=data)  # -> SET DATA


@deriveCard.message(DeriveCardStates.cardNumber)
async def _amount(message: Message, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    await message.delete()

    if message.text is not None:
        claim.setCardAwaitingTo(_str=message.text)

    if claim.cardAwaitingTo:

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        mainMsg: Message = await message.answer(text=Message_text.derive.DeriveCard.amount.format(__BANK__=data["bank"],
                                                                                                  __CARD__=claim.cardAwaitingTo,
                                                                                                  __PHONE__=claim.phoneNumber))
        data["mainMsg"] = mainMsg.message_id
        data['claim'] = claim

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

            if "errMsg" in data:
                await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
                del data["errMsg"]

            description: str = Message_text.derive.DeriveCard.result.format(__PHONE__=claim.phoneNumber,
                                                                            __CARD__=claim.cardAwaitingTo,
                                                                            __AMOUNT__=claim.finalAmount,
                                                                            __AMOUNT_USD__=claim.targetAmount,
                                                                            __COURSE__=claim.exchangeAppliedRate,
                                                                            __BANK__=data["bank"][:-1],
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

            await state.set_state(DeriveCardStates.paid)
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


@deriveCard.callback_query(F.data == "done", DeriveCardStates.paid)
async def _payment(callback: CallbackQuery, state: FSMContext, bot: Bot, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setApproved()
    data['claim'] = claim
    data['timeLeft'] = (data['timeLeft'] - int(time.time())) // 60

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await bot.edit_message_text(reply_markup=None, message_id=data["mainMsg"], chat_id=callback.message.chat.id,
                                text=Message_text.derive.DeriveCard.application.format(__PHONE__=claim.phoneNumber,
                                                                                       __CARD__=claim.cardAwaitingTo,
                                                                                       __AMOUNT__=claim.finalAmount,
                                                                                       __AMOUNT_USD__=claim.targetAmount,
                                                                                       __COURSE__=claim.exchangeAppliedRate,
                                                                                       __BANK__=data["bank"],
                                                                                       __BID_NUMBER__=data['claimId'],
                                                                                       __TIME_LEFT__=data['timeLeft']))

    await callback.message.answer(text=Message_text.derive.DeriveCard.instruction, reply_markup=InlineKeyboardBuilder(
        [[InlineKeyboardButton(text="Оплачено", callback_data="paid")]]).as_markup())

    await state.set_data(data=data)  # -> SET DATA


@deriveCard.callback_query(F.data == "paid", DeriveCardStates.paid)
async def _paid(callback: CallbackQuery, state: FSMContext, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setInitialized()
    data['claim'] = claim

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await callback.message.delete()
    await callback.message.answer(text=Message_text.service_text.UserMessageText.cheque)

    await state.set_state(DeriveCardStates.cheque)
    await state.set_data(data=data)  # -> SET DATA


@deriveCard.message(DeriveCardStates.cheque)
async def _cheque(message: Message, state: FSMContext, bot: Bot, pool: Pool):
    receipt: File | None = None
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    if message.document:
        receipt = await bot.get_file(message.document.file_id)
    elif message.photo:
        receipt = await bot.get_file(message.photo.pop().file_id)

    if receipt:
        claim.setReceiptType(receipt.file_path)
        claim.setReceiptSize(receipt.file_size)
        claim.setReceiptBinary((await bot.download_file(receipt.file_path)).read())

        db: Database = Database(pool)
        await db.updateClaimById(data['claimId'], {'receipt_type': claim.receiptType,
                                                   'receipt_size': claim.receiptSize,
                                                   'receipt_file': claim.receiptBinary})

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
