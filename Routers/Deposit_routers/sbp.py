from math import ceil

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, CallbackQuery, Document, ReplyKeyboardMarkup, \
    File
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiomysql import Pool

from Misc.User_text import Buttons_text, Message_text
from Utils import GetCourse, cancel
from params import USD, FEE
from DataBase import Database
from Entities import Claim

import asyncio
import re
import time

sbp: Router = Router()


class SBPDepositStates(StatesGroup):
    wallet: State = State()
    amount: State = State()
    phoneNumber: State = State()
    paid: State = State()
    cheque: State = State()


@sbp.callback_query(F.data == Buttons_text.deposit.Deposit.sbp.value)
async def _sbp(callback: CallbackQuery, state: FSMContext):
    claim: Claim = Claim()
    claim.setDebit()
    claim.setCurrencyA('RUB')
    claim.setCurrencyB('USD')
    data: dict[str, Claim] = {'claim': claim}

    inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
        [[InlineKeyboardButton(text=btnTxt.value, callback_data=f"{btnTxt.value}_wallet") for btnTxt in
          Buttons_text.deposit.DepositSBP]])
    inlineKeyboard.adjust(2)

    await callback.message.delete()
    await callback.message.answer(text=Message_text.sbp.SBP.chooseWallet,
                                  reply_markup=inlineKeyboard.as_markup())

    await state.set_state(SBPDepositStates.wallet)
    await state.set_data(data=data)  # -> SET DATA


@sbp.callback_query(F.data.split("_")[-1] == "wallet", SBPDepositStates.wallet)
async def _wallet(callback: CallbackQuery, state: FSMContext):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setCurrencyA(callback.data.split("_")[0])

    await callback.message.delete()

    mainMsg: Message = await callback.message.answer(text=Message_text.sbp.SBP.amount.format(__WALLET__=claim.currencyA))

    data['mainMsg']: str = mainMsg.message_id

    await state.set_state(SBPDepositStates.amount)
    await state.set_data(data=data)  # -> SET DATA


@sbp.message(SBPDepositStates.amount)
async def _amount(message: Message, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    if message.text is not None:
        claim.setTargetAmount(amount=message.text)

    if claim.targetAmount >= 1500:

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.sharePhoneNumber, request_contact=True),
              KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        keyboard.adjust(1)
        mainMsg: Message = await message.answer(reply_markup=keyboard.as_markup(resize_keyboard=True),
                                                text=Message_text.sbp.SBP.phoneNumber.format(
                                                    __WALLET__=claim.currencyA, __AMOUNT__=claim.targetAmount))

        data["mainMsg"] = mainMsg.message_id

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(SBPDepositStates.phoneNumber)

    else:

        await message.delete()
        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.sbp.SBP.amountError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@sbp.message(SBPDepositStates.phoneNumber)
async def _phoneNumber(message: Message, bot: Bot, state: FSMContext, pool: Pool):
    data = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    await message.delete()

    if message.contact is not None:
        claim.setPhoneNumber(message.contact.phone_number)
    elif message.text is not None:
        claim.setPhoneNumber(message.text)

    if claim.phoneNumber:
        data['timeLeft'] = int(time.time()) + 1200
        claim.setExchangeAppliedRate(await GetCourse(*USD)())
        claim.setFee(FEE)
        claim.setFinalAmount(ceil(claim.targetAmount / claim.exchangeAppliedRate + claim.fee))
        claim.setCreated()
        description: str = Message_text.sbp.SBP.result.format(__WALLET__=claim.currencyA, __PHONE__=claim.phoneNumber,
                                                              __AMOUNT_USD__=claim.finalAmount,
                                                              __COURSE__=claim.exchangeAppliedRate,
                                                              __AMOUNT__=claim.targetAmount,
                                                              __TIME_LEFT__=20)
        claim.setDescription(description)

        bd: Database = Database(pool)
        claimId: str = await bd.insertСlaim(claim.getAllAttr())
        data["claimId"]: str = claimId

        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])  # del MainMsg
        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        await message.answer(text="Спасибо!", reply_markup=keyboard.as_markup(resize_keyboard=True))

        mainMsg: Message = await message.answer(text=description,
                                                reply_markup=InlineKeyboardBuilder(
                                                    [[InlineKeyboardButton(text="Подтвердить",
                                                                           callback_data="done")]]).as_markup())

        data["mainMsg"] = mainMsg.message_id  # set MainMsg

        cancelOrder: asyncio.Task = asyncio.create_task(cancel(bot, data["mainMsg"], message.chat.id, state))
        data["cancelTask"]: asyncio.Task = cancelOrder

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(SBPDepositStates.paid)
        await state.set_data(data=data)  # -> SET DATA
        await cancelOrder

    else:

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.phoneNumberError)
            data["errMsg"]: str = errorMessage.message_id

            await state.set_data(data=data)  # -> SET DATA


@sbp.callback_query(F.data == "done", SBPDepositStates.paid)
async def _payment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setApproved()
    data['claim'] = claim
    data['timeLeft'] = (data['timeLeft'] - int(time.time())) // 60

    await bot.edit_message_text(
        text=Message_text.sbp.SBP.application.format(__WALLET__=claim.currencyA, __PHONE__=claim.phoneNumber,
                                                     __AMOUNT_USD__=claim.finalAmount,
                                                     __COURSE__=claim.exchangeAppliedRate,
                                                     __AMOUNT__=claim.targetAmount,
                                                     __TIME_LEFT__=data['timeLeft'],
                                                     __BID_NUMBER__=data['claimId']),
        message_id=data["mainMsg"], chat_id=callback.message.chat.id)

    await callback.message.answer(text=Message_text.sbp.SBP.sbpInstruction.format(__AMOUNT_USD__=claim.finalAmount,
                                                                                  __AMOUNT__=claim.targetAmount),
                                  reply_markup=InlineKeyboardBuilder(
                                      [[InlineKeyboardButton(text="Оплачено", callback_data="paid")]]).as_markup())

    await state.set_data(data=data)  # -> SET DATA


@sbp.callback_query(F.data == "paid", SBPDepositStates.paid)
async def _paid(callback: CallbackQuery, state: FSMContext, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setInitialized()
    data['claim'] = claim

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await callback.message.delete()
    await callback.message.answer(text=Message_text.service_text.UserMessageText.cheque)

    await state.set_state(SBPDepositStates.cheque)
    await state.set_data(data=data)  # -> SET DATA


@sbp.message(SBPDepositStates.cheque)
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
        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.service_text.UserMessageText.chequeError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA
