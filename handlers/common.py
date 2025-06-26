from datetime import datetime
from aiogram.types import Message
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from services.ai_service import AIService
from database.models import add_user, add_message, get_user_onboarding_status
from handlers.rating import register_user_activity, start_new_session, RatingStates
from handlers.onboarding import start_onboarding
from config.settings import settings
from services.session_analyzer import add_message_to_session

common_router = Router()

ai_service = AIService()

# Функция для проверки, является ли чат группой менеджеров
def is_manager_group(message: Message) -> bool:
    return message.chat.id == settings.MANAGER_CHAT_ID and message.chat.type != 'private'

@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    # Получаем данные о пользователе
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Добавляем пользователя в базу данных
    try:
        await add_user(user_id, username, first_name, last_name)
    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
    
    # Проверяем, прошел ли пользователь онбординг
    onboarding_completed = await get_user_onboarding_status(user_id)
    
    if not onboarding_completed:
        # Если пользователь новый или не завершил онбординг, запускаем процесс
        await start_onboarding(message, state)
    else:
        # Если пользователь уже прошел онбординг, отправляем обычное приветствие
        await message.answer("""Привет! 👋
Я нейроассистент и готов ответить на любой ваш вопрос.
Сейчас я работаю в тестовом режиме, не злитесь на меня, пожалуйста, если я не смогу ответить. Обещаю, что исправлюсь🤗

❗️ Что я умею?
- Ответить на часто задаваемые вопросы по учебному процессу.
- Помочь с выбором курса под ваши задачи и цели.
- Помочь в решении организационных вопросов.""")

    
@common_router.message(Command(commands=['help']))
async def cmd_help(message: Message):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    # Регистрируем активность пользователя
    register_user_activity(message.chat.id)
    
    await message.answer("""Я могу ответить на часто задаваемые вопросы по учебному процессу, помочь с выбором курса под ваши задачи и цели, а также помочь в решении организационных вопросов.""")
    
# Используем только фильтр F.text без дополнительных условий
@common_router.message(F.text)
async def cmd_message(message: Message, state: FSMContext):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    # Проверяем, не является ли сообщение командой
    if message.text.startswith('/'):
        return
    
    # Проверяем, не находится ли пользователь в состоянии ожидания отзыва
    current_state = await state.get_state()
    if current_state == RatingStates.waiting_for_feedback.state:
        return
        
    # Регистрируем активность пользователя
    register_user_activity(message.chat.id)
    
    # Используем глобальный экземпляр ai_service вместо создания нового
    try:
        # Получаем ответ от AI с передачей user_id
        answer = await ai_service.get_answer(message.text, user_id=str(message.from_user.id))
        
        # Сохраняем сообщение и ответ в базу данных
        try:
            message_id = await add_message(message.from_user.id, message.text, answer)
        except Exception as e:
            print(f"Ошибка при сохранении сообщения: {e}")
            message_id = None
        
        # Отправляем ответ пользователю
        bot_message = await message.answer(answer)
        
        # Добавляем сообщение в сессию для анализа
        await add_message_to_session(message.from_user.id, message.text, answer)
        
        # Начинаем новую сессию для оценки
        if message_id:
            # Получаем бот из контекста сообщения
            bot = message.bot
            await start_new_session(message.chat.id, message_id, bot)
        
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке вашего запроса: {str(e)}")
