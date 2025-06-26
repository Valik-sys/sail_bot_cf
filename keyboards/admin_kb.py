from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🗓 Сегментированная рассылка")],
            [KeyboardButton(text="🗑 Удалить пользователя")],  # Новая кнопка
            [KeyboardButton(text="❌ Выход из админ-панели")]
        ],
        resize_keyboard=True
    )
    return keyboard

    
def get_admin_back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_broadcast_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Подтвердить", callback_data="broadcast:confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast:cancel")]
        ]
    )
    return keyboard

def get_segment_keyboard():
    """Клавиатура для выбора типа сегментации"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌍 По стране")],
            [KeyboardButton(text="🎯 По интересам")],
            [KeyboardButton(text="📚 По предмету")],
            [KeyboardButton(text="👥 Всем пользователям")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_segment_selection_keyboard(options):
    """Клавиатура для выбора конкретного значения сегмента"""
    # Формируем кнопки из доступных опций
    buttons = []
    for option in options:
        buttons.append([KeyboardButton(text=option)])
    
    # Добавляем кнопку "Назад"
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard
