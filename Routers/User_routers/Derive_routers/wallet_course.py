from aiogram import F, Router
from aiogram.types import CallbackQuery
from Misc.User_text import Buttons_text, Message_text
from Utils import GetCourse
from params import USD, FEE


deriveWallet: Router = Router()


@deriveWallet.callback_query(F.data == Buttons_text.derive.Derive.course.value)
async def _course(callback: CallbackQuery):
    usdCourse: float = await GetCourse(*USD)() - FEE
    await callback.message.edit_text(text=Message_text.course.CourseText.courses.format(
        __COURSE__=usdCourse,
        __COURSE_CASH__=usdCourse - 1
    ))

    await callback.answer()
