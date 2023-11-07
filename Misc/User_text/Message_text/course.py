from dataclasses import dataclass


@dataclass
class CourseText:
    courses: str = \
'''
Текущий курс обмена @pyyplrubot:

💳 Карты:
 1$ = {__COURSE__} ₽

🔄 СБП:
1$ = {__COURSE__} ₽

💸 Наличные:
 1$ = {__COURSE_CASH__} ₽

❕ Курс рассчитывается автоматически и может измениться на момент формирования сделки
'''
