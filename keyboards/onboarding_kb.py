from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_skip_keyboard():
    """Клавиатура с кнопкой пропуска"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_country_keyboard():
    '''Клавиатура с вариантами стран'''
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Беларусь🇧🇾'), KeyboardButton(text='Россия🇷🇺')],
            [KeyboardButton(text='Украина🇺🇦'), KeyboardButton(text='Казахстан🇰🇿')],
            [KeyboardButton(text='Страна Европы🇪🇺'), KeyboardButton(text='Другая страна🌍')],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_interests_keyboard():
    """Клавиатура с вариантами интересов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нейросети"), KeyboardButton(text="блог учителя")],
            [KeyboardButton(text="Canva и онлайн-сервисы для работы"), KeyboardButton(text="Налоги и правовые аспекты для юристов РБ")],
            [KeyboardButton(text="Старт в онлайн")],
            [KeyboardButton(text="Автоматизация и экономия времени"), KeyboardButton(text="Учебные материалы")],
            [KeyboardButton(text="Пропустить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_subjects_keyboard():
    """Клавиатура с вариантами предметов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Математика"), KeyboardButton(text="Русский язык")],
            [KeyboardButton(text="Английский язык"), KeyboardButton(text="Информатика")],
            [KeyboardButton(text="История"), KeyboardButton(text="Биология")],
            [KeyboardButton(text="Физика"), KeyboardButton(text="Химия")],
            [KeyboardButton(text="Белорусский язык"), KeyboardButton(text="Другой предмет")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard