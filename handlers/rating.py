import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.rating_kb_inline import get_rating_keyboard, get_feedback_keyboard
from database.models import add_rating
from config.settings import settings

# Создаем роутер для обработки оценок
rating_router = Router()

# Определяем состояния для FSM (конечного автомата)
class RatingStates(StatesGroup):
    waiting_for_feedback = State()  # Ожидание текстового отзыва

# Функция для проверки, является ли чат группой менеджеров
def is_manager_group(message_or_callback):
    if hasattr(message_or_callback, 'message'):
        # Это callback_query
        chat = message_or_callback.message.chat
    else:
        # Это message
        chat = message_or_callback.chat
    
    return chat.id == settings.MANAGER_CHAT_ID and chat.type != 'private'

# Словарь для хранения активных сессий и таймеров
active_sessions = {}

async def start_rating_timer(chat_id, message_id, bot):
    """
    Запускает таймер для отправки запроса на оценку через 3 минуты.
    
    Args:
        chat_id (int): ID чата пользователя
        message_id (int): ID сообщения, которое нужно оценить
        bot: Экземпляр бота для отправки сообщений
    """
    # Ждем 3 минуты
    await asyncio.sleep(180)  # 180 секунд = 3 минуты
    
    # Проверяем, активна ли еще сессия
    if chat_id in active_sessions and active_sessions[chat_id]['message_id'] == message_id:
        # Отправляем запрос на оценку
        rating_message = await bot.send_message(
            chat_id=chat_id,
            text="Пожалуйста, оцените мой ответ от 1 до 5 звезд:",
            reply_markup=get_rating_keyboard()
        )
        
        # Обновляем информацию о сессии
        active_sessions[chat_id]['rating_message_id'] = rating_message.message_id
        
        # Удаляем сессию через 10 минут, если пользователь не оценил
        asyncio.create_task(clear_session_after_timeout(chat_id, 600))  # 600 секунд = 10 минут

async def clear_session_after_timeout(chat_id, timeout):
    """
    Удаляет сессию после указанного таймаута, если пользователь не ответил.
    
    Args:
        chat_id (int): ID чата пользователя
        timeout (int): Время ожидания в секундах
    """
    await asyncio.sleep(timeout)
    if chat_id in active_sessions:
        del active_sessions[chat_id]
        print(f"Сессия для пользователя {chat_id} удалена по таймауту")

def register_user_activity(chat_id):
    """
    Регистрирует активность пользователя, сбрасывая таймер оценки.
    
    Args:
        chat_id (int): ID чата пользователя
    """
    if chat_id in active_sessions:
        # Обновляем время последней активности
        active_sessions[chat_id]['last_activity'] = datetime.now()

async def start_new_session(chat_id, message_id, bot):
    """
    Начинает новую сессию для пользователя.
    
    Args:
        chat_id (int): ID чата пользователя
        message_id (int): ID сообщения бота
        bot: Экземпляр бота
    """
    # Если уже есть активная сессия, удаляем её
    if chat_id in active_sessions:
        # Отменяем существующие задачи
        if 'timer_task' in active_sessions[chat_id]:
            active_sessions[chat_id]['timer_task'].cancel()
    
    # Создаем новую сессию
    timer_task = asyncio.create_task(start_rating_timer(chat_id, message_id, bot))
    
    active_sessions[chat_id] = {
        'message_id': message_id,
        'last_activity': datetime.now(),
        'timer_task': timer_task
    }

@rating_router.callback_query(F.data.startswith("rate:"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает оценку пользователя.
    
    Args:
        callback (CallbackQuery): Данные обратного вызова
        state (FSMContext): Контекст состояния FSM
    """
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(callback):
        return
        
    # Извлекаем оценку из callback_data
    rating_value = callback.data.split(":")[1]
    
    if rating_value == "skip":
        # Пользователь решил не оценивать
        await callback.message.edit_text("Спасибо! Вы можете оценить ответ позже.")
        
        # Удаляем сессию
        if callback.message.chat.id in active_sessions:
            del active_sessions[callback.message.chat.id]
        
        return
    
    # Преобразуем оценку в число
    rating = int(rating_value)
    
    # Получаем информацию о сессии
    chat_id = callback.message.chat.id
    message_id = None
    
    if chat_id in active_sessions:
        message_id = active_sessions[chat_id]['message_id']
    
    # Сохраняем оценку и message_id в состоянии FSM
    await state.update_data(rating=rating, message_id=message_id)
    
    # Сохраняем оценку в базе данных
    if message_id:
        try:
            await add_rating(message_id, callback.from_user.id, rating)
            print(f"Оценка {rating} сохранена для сообщения {message_id}")  # Отладочное сообщение
        except Exception as e:
            print(f"Ошибка при сохранении оценки: {e}")
    
    # Благодарим пользователя и предлагаем оставить отзыв для оценок ниже 4
    if rating < 4:
        await callback.message.edit_text(
            f"Спасибо за вашу оценку ({rating}/5)! Хотели бы вы оставить комментарий, чтобы мы могли улучшить наш сервис?",
            reply_markup=get_feedback_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"Спасибо за вашу высокую оценку ({rating}/5)! Мы рады, что смогли вам помочь."
        )
        
        # Удаляем сессию
        if chat_id in active_sessions:
            del active_sessions[chat_id]
    
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()

@rating_router.callback_query(F.data.startswith("feedback:"))
async def process_feedback_request(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает запрос на оставление отзыва.
    
    Args:
        callback (CallbackQuery): Данные обратного вызова
        state (FSMContext): Контекст состояния FSM
    """
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(callback):
        return
        
    action = callback.data.split(":")[1]
    
    if action == "skip":
        # Пользователь решил не оставлять отзыв
        await callback.message.edit_text("Спасибо за вашу оценку! Будем рады помочь вам снова.")
        
        # Сбрасываем состояние
        await state.clear()
        
        # Удаляем сессию
        if callback.message.chat.id in active_sessions:
            del active_sessions[callback.message.chat.id]
    else:
        # Пользователь хочет оставить отзыв
        await callback.message.edit_text("Пожалуйста, напишите ваш отзыв в следующем сообщении:")
        
        # Устанавливаем состояние ожидания отзыва
        await state.set_state(RatingStates.waiting_for_feedback)
        
        print(f"Установлено состояние ожидания отзыва для пользователя {callback.message.chat.id}")  # Отладочное сообщение
    
    # Отвечаем на callback
    await callback.answer()

@rating_router.message(RatingStates.waiting_for_feedback)
async def process_feedback(message: Message, state: FSMContext):
    """
    Обрабатывает текстовый отзыв пользователя.
    
    Args:
        message (Message): Сообщение с отзывом
        state (FSMContext): Контекст состояния FSM
    """
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    print(f"Функция process_feedback вызвана для пользователя {message.from_user.id}")
    
    # Получаем данные из состояния
    data = await state.get_data()
    rating = data.get("rating", 0)
    
    # Получаем текст отзыва
    feedback_text = message.text
    
    print(f"Получен отзыв: {feedback_text} с оценкой {rating}")  # Отладочное сообщение
    
    # Получаем информацию о сессии
    chat_id = message.chat.id
    message_id = data.get("message_id")  # Получаем message_id из состояния
    
    print(f"message_id из состояния: {message_id}")
    
    if not message_id and chat_id in active_sessions:
        message_id = active_sessions[chat_id].get('message_id')
        print(f"message_id из active_sessions: {message_id}")
    
    # Обновляем оценку в базе данных, добавляя отзыв
    if message_id:
        try:
            await add_rating(message_id, message.from_user.id, rating, feedback_text)
            print(f"Отзыв сохранен в базе данных для сообщения {message_id}")  # Отладочное сообщение
        except Exception as e:
            print(f"Ошибка при сохранении отзыва: {e}")
    else:
        print("Не удалось найти ID сообщения для сохранения отзыва")
    
    # Благодарим пользователя за отзыв
    await message.answer("Спасибо за ваш отзыв! Мы обязательно учтем его для улучшения нашего сервиса.")
    
    # Сбрасываем состояние
    await state.clear()
    print(f"Состояние сброшено для пользователя {message.from_user.id}")
    
    # Удаляем сессию
    if chat_id in active_sessions:
        del active_sessions[chat_id]
        print(f"Сессия удалена для пользователя {chat_id}")

# Команда для принудительного запроса оценки (для тестирования)
@rating_router.message(Command("rate"))
async def cmd_rate(message: Message):
    """
    Команда для принудительного запроса оценки (для тестирования).
    
    Args:
        message (Message): Сообщение с командой
    """
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    print("Получена команда /rate")  # Отладочное сообщение
    await message.answer(
        "Пожалуйста, оцените качество ответов бота от 1 до 5 звезд:",
        reply_markup=get_rating_keyboard()
    )
