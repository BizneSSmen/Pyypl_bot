from aiogram import F, Router
from aiogram.types import CallbackQuery
from Misc.User_text import Buttons_text, Message_text
from Utils import GetCourse
from params import USD, FEE


depositWallet: Router = Router()


@depositWallet.callback_query(F.data == Buttons_text.deposit.Deposit.course.value)
async def _course(callback: CallbackQuery):
    usdCourse: float = await GetCourse(*USD)() + FEE
    await callback.message.edit_text(text=Message_text.course.CourseText.courses.format(
        __COURSE__=usdCourse,
        __COURSE_CASH__=usdCourse - 1
    ))

    await callback.answer()
