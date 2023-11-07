import time
from math import ceil

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, CallbackQuery, Document, ReplyKeyboardMarkup, File
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiomysql import Pool

from Misc.User_text import Buttons_text, Message_text
from DataBase import Database
from Entities import Claim
from Utils import GetCourse, cancel
from params import USD, FEE
import asyncio

depositCard: Router = Router()


class CardDepositStates(StatesGroup):
    bank: State = State()
    cardNumber: State = State()
    amount: State = State()
    phoneNumber: State = State()
    paid: State = State()
    cheque: State = State()


@depositCard.callback_query(F.data == Buttons_text.deposit.Deposit.card.value)
async def _chooseBank(callback: CallbackQuery, state: FSMContext):
    claim: Claim = Claim()
    claim.setDebit()
    claim.setCurrencyA('RUB')
    claim.setCurrencyB('USD')
    data: dict[str, Claim] = {'claim': claim}

    inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
        [[InlineKeyboardButton(text=btnTxt.value, callback_data=f"{btnTxt.value}_bank") for btnTxt in
          Buttons_text.deposit.DepositCard]])
    inlineKeyboard.adjust(2)

    await callback.message.delete()
    await callback.message.answer(text=Message_text.deposit.Deposit.chooseBank,
                                  reply_markup=inlineKeyboard.as_markup())

    await state.set_state(CardDepositStates.bank)
    await state.set_data(data=data)  # -> SET DATA


@depositCard.callback_query(F.data.split("_")[-1] == "bank", CardDepositStates.bank)
async def _cardNumber(callback: CallbackQuery, state: FSMContext):
    data: dict = await state.get_data()  # <- GET DATA
    data['bank'] = callback.data.split("_")[0]

    await callback.message.delete()

    mainMsg: Message = await callback.message.answer(
        text=Message_text.deposit.Deposit.cardNumber.format(__BANK__=data['bank']))

    data['mainMsg']: str = mainMsg.message_id

    await state.set_state(CardDepositStates.cardNumber)
    await state.set_data(data=data)  # -> SET DATA


@depositCard.message(CardDepositStates.cardNumber)
async def _amount(message: Message, state: FSMContext, bot: Bot):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    if message.text is not None:
        claim.setCardPaidFromNumber(_str=message.text)

    if claim.cardPaidFrom:

        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        mainMsg: Message = await message.answer(text=Message_text.deposit.Deposit.amount.format(__BANK__=data["bank"],
                                                                                                __CARD__=claim.cardPaidFrom))

        data["mainMsg"] = mainMsg.message_id
        data['claim'] = claim

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(CardDepositStates.amount)

    else:
        await message.delete()
        data: dict = await state.get_data()

        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.cardError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@depositCard.message(CardDepositStates.amount)
async def _phoneNumber(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    if message.text is not None:
        claim.setTargetAmount(amount=message.text)

    if claim.targetAmount >= 1500:

        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])

        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.sharePhoneNumber, request_contact=True),
              KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        keyboard.adjust(1)
        mainMsg: Message = await message.answer(reply_markup=keyboard.as_markup(resize_keyboard=True),
                                                text=Message_text.deposit.Deposit.phoneNumber.format(
                                                    __BANK__=data["bank"], __CARD__=claim.cardPaidFrom,
                                                    __AMOUNT__=claim.targetAmount))

        data["mainMsg"] = mainMsg.message_id
        data['claim'] = claim

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(CardDepositStates.phoneNumber)

    else:
        await message.delete()
        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.amountError)
            data["errMsg"]: str = errorMessage.message_id

    await state.set_data(data=data)  # -> SET DATA


@depositCard.message(CardDepositStates.phoneNumber)
async def _accept(message: Message, state: FSMContext, bot: Bot, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    if message.contact is not None:
        claim.setPhoneNumber(message.contact.phone_number)
    elif message.text is not None:
        claim.setPhoneNumber(message.text)

    if claim.phoneNumber:

        claim.setExchangeAppliedRate(await GetCourse(*USD)())
        claim.setFee(FEE)
        claim.setCreated()
        claim.setFinalAmount(ceil(claim.targetAmount / claim.exchangeAppliedRate + claim.fee))
        data['timeLeft'] = int(time.time()) + 1200
        description = Message_text.deposit.Deposit.result.format(__BANK__=data["bank"][:-1],
                                                                 __CARD__=claim.cardPaidFrom,
                                                                 __PHONE__=claim.phoneNumber,
                                                                 __AMOUNT_USD__=claim.finalAmount,
                                                                 __COURSE__=claim.exchangeAppliedRate + claim.fee,
                                                                 __AMOUNT__=claim.targetAmount, __TIME_LEFT__=20)
        claim.setDescription(description)
        bd: Database = Database(pool)
        claimId: str = await bd.insertСlaim(claim.getAllAttr())
        data["claimId"]: str = claimId

        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=data["mainMsg"])  # del MainMsg
        keyboard: ReplyKeyboardBuilder = ReplyKeyboardBuilder(
            [[KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)]])
        await message.answer(text="Спасибо!", reply_markup=keyboard.as_markup(resize_keyboard=True))

        mainMsg: Message = await message.answer(
            text=description, reply_markup=InlineKeyboardBuilder(
                [[InlineKeyboardButton(text="Подтвердить", callback_data="done")]]).as_markup())

        cancelOrder: asyncio.Task = asyncio.create_task(cancel(bot, data["mainMsg"], message.chat.id, state))
        data["cancelTask"]: asyncio.Task = cancelOrder
        data["mainMsg"] = mainMsg.message_id  # set MainMsg
        data['claim'] = claim

        if "errMsg" in data:
            await bot.delete_message(chat_id=message.chat.id, message_id=data["errMsg"])
            del data["errMsg"]

        await state.set_state(CardDepositStates.paid)
        await state.set_data(data=data)  # -> SET DATA
        await cancelOrder

    else:

        await message.delete()
        if "errMsg" not in data:
            errorMessage: Message = await message.answer(text=Message_text.deposit.Deposit.phoneNumberError)
            data["errMsg"]: str = errorMessage.message_id

            await state.set_data(data=data)  # -> SET DATA


@depositCard.callback_query(F.data == "done", CardDepositStates.paid)
async def _payment(callback: CallbackQuery, state: FSMContext, bot: Bot, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setApproved()
    data['claim'] = claim
    data['timeLeft'] = (data['timeLeft'] - int(time.time())) // 60

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await bot.edit_message_text(
        text=Message_text.deposit.Deposit.application.format(__BANK__=data["bank"],
                                                             __CARD__=claim.cardPaidFrom,
                                                             __PHONE__=claim.phoneNumber,
                                                             __AMOUNT_USD__=claim.finalAmount,
                                                             __COURSE__=claim.exchangeAppliedRate + claim.fee,
                                                             __AMOUNT__=claim.targetAmount,
                                                             __BID_NUMBER__=data['claimId'],
                                                             __TIME_LEFT__=data['endDate']),
        reply_markup=None, message_id=data["mainMsg"], chat_id=callback.message.chat.id)

    await callback.message.answer(
        text=Message_text.deposit.Deposit.cardInstruction.format(__AMOUNT_USD__=claim.finalAmount
                                                                 , __AMOUNT__=claim.targetAmount),
        reply_markup=InlineKeyboardBuilder(
            [[InlineKeyboardButton(text="Оплачено", callback_data="paid")]]).as_markup())

    await state.set_data(data=data)  # -> SET DATA


@depositCard.callback_query(F.data == "paid", CardDepositStates.paid)
async def _paid(callback: CallbackQuery, state: FSMContext, pool: Pool):
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']
    claim.setInitialized()
    data['claim'] = claim

    db: Database = Database(pool)
    await db.updateClaimById(data['claimId'], {'status': claim.status})

    await callback.message.delete()
    await callback.message.answer(text=Message_text.service_text.UserMessageText.cheque)

    await state.set_state(CardDepositStates.cheque)
    await state.set_data(data=data)  # -> SET DATA


@depositCard.message(CardDepositStates.cheque)
async def _cheque(message: Message, state: FSMContext, bot: Bot, pool: Pool):
    receipt: File | None = None
    data: dict = await state.get_data()  # <- GET DATA
    claim: Claim = data['claim']

    if message.document:
        receipt = await bot.get_file(message.document.file_id)
    elif message.photo:
        receipt = await bot.get_file(message.photo.pop().file_id)

    if claim.setReceiptType(receipt.file_path):
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
