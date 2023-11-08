from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from Misc.User_text import Buttons_text, Message_text
from aiogram.fsm.context import FSMContext

mainMenu: Router = Router()


@mainMenu.message(Command("start"))
async def _start(message: Message, state: FSMContext):

    await state.clear()

    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=btnTxt.value) for btnTxt in list(Buttons_text.main_menu.MainMenu)[:2]]] +
                                            [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[2].value)]] +
                                            [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[3].value)]],
                                   resize_keyboard=True)
    await message.answer(reply_markup=keyboard,
                         text=Message_text.service_text.UserMessageText.helloTxt.format(
                             __NAME__=message.from_user.first_name))


@mainMenu.message(F.text == Buttons_text.service.ServiceButtonText.cancel)
async def _cancel(message: Message, state: FSMContext):
    try:
        data: dict = await state.get_data()  # <- GET DATA
        data["cancelTask"].cancel()
    except:
        pass
    await state.clear()

    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=btnTxt.value) for btnTxt in list(Buttons_text.main_menu.MainMenu)[:2]]] +
                                            [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[2].value)]] +
                                            [[KeyboardButton(text=list(Buttons_text.main_menu.MainMenu)[3].value)]],
                                   resize_keyboard=True)
    await message.answer(text=Message_text.service_text.UserMessageText.cancel,
                         reply_markup=keyboard)


# Deposit

@mainMenu.message(F.text == Buttons_text.main_menu.MainMenu.deposit.value)
async def _deposit(message: Message):

    keyboardButton: ReplyKeyboardBuilder = (ReplyKeyboardBuilder().
                                            add(KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)))
    await message.answer(text=Message_text.deposit.Deposit.keyboardChangeMsg,
                         reply_markup=keyboardButton.as_markup(resize_keyboard=True))

    inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
        [[InlineKeyboardButton(text=btnTxt.value, callback_data=btnTxt.value) for btnTxt in
          Buttons_text.deposit.Deposit]])
    inlineKeyboard.adjust(1)
    await message.answer(text=Message_text.deposit.Deposit.chooseWay, reply_markup=inlineKeyboard.as_markup())


# Derive


@mainMenu.message(F.text == Buttons_text.main_menu.MainMenu.derive.value)
async def _derive(message: Message):
    keyboardButton: ReplyKeyboardBuilder = (ReplyKeyboardBuilder().
                                            add(KeyboardButton(text=Buttons_text.service.ServiceButtonText.cancel)))
    await message.answer(text=Message_text.derive.DeriveCard.keyboardChangeMsg,
                         reply_markup=keyboardButton.as_markup(resize_keyboard=True))

    inlineKeyboard: InlineKeyboardBuilder = InlineKeyboardBuilder(
        [[InlineKeyboardButton(text=btnTxt.value, callback_data=btnTxt.value) for btnTxt in
          Buttons_text.derive.Derive]])
    inlineKeyboard.adjust(1)
    await message.answer(text=Message_text.deposit.Deposit.chooseWay, reply_markup=inlineKeyboard.as_markup())


# FAQ

@mainMenu.message(F.text == Buttons_text.main_menu.MainMenu.faq.value)
async def _faq(message: Message):
    await message.answer(text=Message_text.service_text.UserMessageText.FAQ, disable_web_page_preview=True)