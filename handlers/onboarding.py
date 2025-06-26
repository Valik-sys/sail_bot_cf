from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import update_user_onboarding, get_user_onboarding_status
from keyboards.onboarding_kb import get_skip_keyboard, get_subjects_keyboard, get_interests_keyboard, get_country_keyboard
from config.settings import settings

onboarding_router = Router() 

class OnboardingStates(StatesGroup):
    waiting_for_country = State()  # Ожидание выбора страны
    waiting_for_interests = State()  # Ожидание выбора интересов
    waiting_for_subject = State()  # Ожидание выбора предмета
    
# Функция для проверки, является ли чат группой менеджеров
def is_manager_group(message):
    return message.chat.id == settings.MANAGER_CHAT_ID and message.chat.type != 'private'
    
async def start_onboarding(message: Message, state: FSMContext):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    await state.set_state(OnboardingStates.waiting_for_country)
    await message.answer(
        """Добро пожаловать! Чтобы я мог лучше помогать вам, ответьте, пожалуйста, на несколько вопросов.

Из какой вы страны?""",
        reply_markup=get_country_keyboard()
    )


@onboarding_router.message(OnboardingStates.waiting_for_country)
async def process_country(message: Message, state: FSMContext):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    if message.text == "Пропустить":
        country = None
    else:
        country = message.text
        await update_user_onboarding(message.from_user.id, country = country)
    
    await state.update_data(country=country)
    await state.set_state(OnboardingStates.waiting_for_interests)
    await message.answer(
        '''Какие темы вас интересуют? Выберите из списка или пропустите этот шаг.''',
        reply_markup=get_interests_keyboard()
    )
    
# Обработчик ответа об интересах
@onboarding_router.message(OnboardingStates.waiting_for_interests)
async def process_interests(message: Message, state: FSMContext):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    # Если пользователь решил пропустить вопрос
    if message.text == "Пропустить":
        interests = None
    else:
        interests = message.text
        await update_user_onboarding(message.from_user.id, interests=interests)
    
    # Сохраняем ответ и переходим к следующему вопросу
    await state.update_data(interests=interests)
    await state.set_state(OnboardingStates.waiting_for_subject)
    
    await message.answer(
        "Какой предмет вы преподаете?",
        reply_markup=get_subjects_keyboard()
    )

# Обработчик ответа о предмете
@onboarding_router.message(OnboardingStates.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext):
    # Игнорируем сообщения из группы менеджеров
    if is_manager_group(message):
        return
        
    # Если пользователь решил пропустить вопрос
    if message.text == "Пропустить":
        subject = None
    else:
        subject = message.text
    
    # Сохраняем ответ и завершаем онбординг
    await state.update_data(subject=subject)
    user_data = await state.get_data()
    
    # Обновляем информацию о пользователе и отмечаем онбординг как завершенный
    await update_user_onboarding(
        message.from_user.id,
        country=user_data.get('country'),
        interests=user_data.get('interests'),
        subject=subject,
        completed=True
    )
    
    # Очищаем состояние и отправляем приветственное сообщение
    await state.clear()
    
    await message.answer(
        "Спасибо за информацию! Теперь я смогу лучше помогать вам.\n\n"
        "Я нейроассистент и готов ответить на любой ваш вопрос. "
        "Сейчас я работаю в тестовом режиме, не злитесь на меня, пожалуйста, если я не смогу ответить. Обещаю, что исправлюсь🤗\n\n"
        "❗️ Что я умею?\n"
        "- Ответить на часто задаваемые вопросы по учебному процессу.\n"
        "- Помочь с выбором курса под ваши задачи и цели.\n"
        "- Помочь в решении организационных вопросов.",
        reply_markup=None
    )
