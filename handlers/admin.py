from aiogram import Router, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.settings import settings
from keyboards.admin_kb import get_admin_main_keyboard, get_admin_back_keyboard, get_broadcast_confirmation_keyboard 
from keyboards.admin_kb import get_segment_keyboard, get_segment_selection_keyboard
from database.admin_models import get_users_count, get_messages_count, get_ratings_stats, get_all_users, get_all_user_ids 
from database.admin_models import get_available_segments, get_users_by_segment, delete_user
from aiogram.types import Chat

def is_admin_filter(message):
    return is_admin(message.from_user.id)

admin_router = Router()

class AdminStates(StatesGroup):
    main_menu = State()  # Главное меню админ-панели
    waiting_for_broadcast_text = State()  # Ожидание текста для рассылки
    confirm_broadcast = State()  # Подтверждение рассылки
    segment_selection = State()  # Выбор сегмента для рассылки
    waiting_for_country = State()  # Ожидание выбора страны
    waiting_for_interests = State()  # Ожидание выбора интересов
    waiting_for_subject = State()  # Ожидание выбора предмета
    waiting_for_user_id = State()  # Ожидание ID пользователя для удаления
    
def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id == settings.ADMIN_ID

@admin_router.message(Command(commands=['admin']))
async def cmd_admin(message:Message,state:FSMContext):
    """Команда для входа в админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    await state.set_state(AdminStates.main_menu)
    await message.answer('Добро пожаловать в админ-панель! Выберите действие:', reply_markup=get_admin_main_keyboard())
    
    
@admin_router.message(AdminStates.main_menu,F.text=="📊 Статистика")
async def admin_statistics(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return 
    
    
    """Показать статистику бота"""
    # Получаем статистику из базы данных
    users_count = await get_users_count()
    messages_count = await get_messages_count()
    ratings_data = await get_ratings_stats()

    
    stats_text = f"📊 <b>Статистика бота</b>\n\n"
    stats_text += f"👥 Пользователей: <b>{users_count}</b>\n"
    stats_text += f"💬 Сообщений: <b>{messages_count}</b>\n"
    stats_text += f"⭐ Оценок: <b>{ratings_data['total_count']}</b>\n"
    
    if ratings_data['total_count'] > 0:
        stats_text += f"📈 Средняя оценка: <b>{ratings_data['avg_rating']}</b>\n\n"
        
        # Добавляем распределение оценок
        stats_text += "<b>Распределение оценок:</b>\n"
        for rating in range(1, 6):
            count = ratings_data['distribution'].get(rating, 0)
            stars = "⭐" * rating
            stats_text += f"{stars}: {count}\n"
    
    await message.answer(stats_text, parse_mode="HTML")
    

@admin_router.message(AdminStates.main_menu, F.text == "🗓 Сегментированная рассылка")
async def admin_segment_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.segment_selection)
    
    # Получаем доступные сегменты
    segments = await get_available_segments()
    
    # Сохраняем сегменты в состоянии
    await state.update_data(available_segments=segments)
    
    await message.answer(
        "Выберите параметр для сегментации аудитории:",
        reply_markup=get_segment_keyboard()
    )

@admin_router.message(AdminStates.segment_selection, F.text == "🌍 По стране")
async def select_country_segment(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    segments = data.get("available_segments", {})
    countries = segments.get("countries", [])
    
    if not countries:
        await message.answer("Нет доступных стран для сегментации. Попробуйте другой параметр.")
        return
    
    await state.set_state(AdminStates.waiting_for_country)
    await message.answer(
        "Выберите страну для рассылки:",
        reply_markup=get_segment_selection_keyboard(countries)
    )

@admin_router.message(AdminStates.segment_selection, F.text == "🎯 По интересам")
async def select_interests_segment(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    segments = data.get("available_segments", {})
    interests = segments.get("interests", [])
    
    if not interests:
        await message.answer("Нет доступных интересов для сегментации. Попробуйте другой параметр.")
        return
    
    await state.set_state(AdminStates.waiting_for_interests)
    await message.answer(
        "Выберите интерес для рассылки:",
        reply_markup=get_segment_selection_keyboard(interests)
    )

@admin_router.message(AdminStates.segment_selection, F.text == "📚 По предмету")
async def select_subject_segment(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    segments = data.get("available_segments", {})
    subjects = segments.get("subjects", [])
    
    if not subjects:
        await message.answer("Нет доступных предметов для сегментации. Попробуйте другой параметр.")
        return
    
    await state.set_state(AdminStates.waiting_for_subject)
    await message.answer(
        "Выберите предмет для рассылки:",
        reply_markup=get_segment_selection_keyboard(subjects)
    )

@admin_router.message(AdminStates.segment_selection, F.text == "👥 Всем пользователям")
async def select_all_users(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    # Сохраняем информацию, что рассылка будет всем пользователям
    await state.update_data(segment_type=None, segment_value=None)
    
    await state.set_state(AdminStates.waiting_for_broadcast_text)
    await message.answer(
        "Введите текст для рассылки всем пользователям:",
        reply_markup=get_admin_back_keyboard()
    )

@admin_router.message(AdminStates.segment_selection, F.text == "⬅️ Назад")
async def segment_selection_back(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.main_menu)
    await message.answer(
        "Вы вернулись в главное меню админ-панели.",
        reply_markup=get_admin_main_keyboard()
    )

@admin_router.message(AdminStates.waiting_for_country)
async def process_country_selection(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    if message.text == "⬅️ Назад":
        await state.set_state(AdminStates.segment_selection)
        await message.answer(
            "Выберите параметр для сегментации аудитории:",
            reply_markup=get_segment_keyboard()
        )
        return
    
    # Сохраняем выбранную страну
    await state.update_data(segment_type="country", segment_value=message.text)
    
    await state.set_state(AdminStates.waiting_for_broadcast_text)
    await message.answer(
        f"Вы выбрали сегмент: пользователи из страны {message.text}\n\n"
        "Введите текст для рассылки:",
        reply_markup=get_admin_back_keyboard()
    )

@admin_router.message(AdminStates.waiting_for_interests)
async def process_interests_selection(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    if message.text == "⬅️ Назад":
        await state.set_state(AdminStates.segment_selection)
        await message.answer(
            "Выберите параметр для сегментации аудитории:",
            reply_markup=get_segment_keyboard()
        )
        return
    
    # Сохраняем выбранный интерес
    await state.update_data(segment_type="interests", segment_value=message.text)
    
    await state.set_state(AdminStates.waiting_for_broadcast_text)
    await message.answer(
        f"Вы выбрали сегмент: пользователи, интересующиеся темой {message.text}\n\n"
        "Введите текст для рассылки:",
        reply_markup=get_admin_back_keyboard()
    )

@admin_router.message(AdminStates.waiting_for_subject)
async def process_subject_selection(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    if message.text == "⬅️ Назад":
        await state.set_state(AdminStates.segment_selection)
        await message.answer(
            "Выберите параметр для сегментации аудитории:",
            reply_markup=get_segment_keyboard()
        )
        return
    
    # Сохраняем выбранный предмет
    await state.update_data(segment_type="subject", segment_value=message.text)
    
    await state.set_state(AdminStates.waiting_for_broadcast_text)
    await message.answer(
        f"Вы выбрали сегмент: преподаватели предмета {message.text}\n\n"
        "Введите текст для рассылки:",
        reply_markup=get_admin_back_keyboard()
    )

@admin_router.message(AdminStates.waiting_for_broadcast_text, F.text =='⬅️ Назад')
async def admin_broadcast_back(message:Message, state:FSMContext):
    if not is_admin(message.from_user.id):
        return
        
    # Проверяем, откуда пришли - из обычной рассылки или сегментированной
    data = await state.get_data()
    segment_type = data.get('segment_type')
        
    if segment_type:
        # Если это сегментированная рассылка, возвращаемся к выбору сегмента
        await state.set_state(AdminStates.segment_selection)
        await message.answer(
            "Выберите параметр для сегментации аудитории:",
            reply_markup=get_segment_keyboard()
        )
    else:
        # Если обычная рассылка, возвращаемся в главное меню
        await state.set_state(AdminStates.main_menu)
        await message.answer(
            "Вы вернулись в главное меню админ-панели.",
            reply_markup=get_admin_main_keyboard()
        )
    
@admin_router.message(AdminStates.waiting_for_broadcast_text, F.text)
async def admin_broadcast_text(message:Message, state:FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    # Сохраняем текст рассылки в состоянии
    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminStates.confirm_broadcast)
    
    # Получаем информацию о сегменте, если есть
    data = await state.get_data()
    segment_type = data.get('segment_type')
    segment_value = data.get('segment_value')
    
    segment_info = ""
    if segment_type:
        if segment_type == "country":
            segment_info = f"Сегмент: пользователи из страны {segment_value}\n\n"
        elif segment_type == "interests":
            segment_info = f"Сегмент: пользователи, интересующиеся темой {segment_value}\n\n"
        elif segment_type == "subject":
            segment_info = f"Сегмент: преподаватели предмета {segment_value}\n\n"
    
    await message.answer(
        f"<b>Предпросмотр сообщения:</b>\n\n{segment_info}{message.text}\n\n"
        f"Отправить это сообщение выбранным пользователям?",
        parse_mode="HTML",
        reply_markup=get_broadcast_confirmation_keyboard()
    )
    
@admin_router.callback_query(AdminStates.confirm_broadcast, F.data == "broadcast:confirm")
async def admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text', '')
    segment_type = data.get('segment_type')
    segment_value = data.get('segment_value')
    
    # Получаем список пользователей в зависимости от выбранного сегмента
    if segment_type:
        if segment_type == "country":
            user_ids = await get_users_by_segment(country=segment_value)
            segment_description = f"из страны {segment_value}"
        elif segment_type == "interests":
            user_ids = await get_users_by_segment(interests=segment_value)
            segment_description = f"интересующихся темой {segment_value}"
        elif segment_type == "subject":
            user_ids = await get_users_by_segment(subject=segment_value)
            segment_description = f"преподающих предмет {segment_value}"
        else:
            user_ids = await get_all_user_ids()
            segment_description = "всем пользователям"
    else:
        user_ids = await get_all_user_ids()
        segment_description = "всем пользователям"
    
    # Отправляем сообщение о начале рассылки
    await callback.message.edit_text(
        f"Начинаю рассылку сообщения {len(user_ids)} пользователям {segment_description}...",
        reply_markup=None
    )
    
    # Счетчики успешных отправок
    success_count = 0
    error_count = 0
    
    # Отправляем сообщения пользователям
    for user_id in user_ids:
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
            error_count += 1
    
    # Отправляем сообщение об окончании рассылки
    await callback.message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"✓ Успешно отправлено: {success_count}\n"
        f"✗ Ошибок: {error_count}",
        parse_mode="HTML"
    )
    
    # Возвращаемся в главное меню
    await state.set_state(AdminStates.main_menu)
    await callback.message.answer(
        "Вы вернулись в главное меню админ-панели.",
        reply_markup=get_admin_main_keyboard()
    )
    
@admin_router.callback_query(AdminStates.confirm_broadcast, F.data == "broadcast:cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа к этой функции.")
        return
    
    await callback.message.edit_text("Рассылка отменена.", reply_markup=None)
    
    # Проверяем, откуда пришли - из обычной рассылки или сегментированной
    data = await state.get_data()
    segment_type = data.get('segment_type')
    
    if segment_type:
        # Если это сегментированная рассылка, возвращаемся к выбору сегмента
        await state.set_state(AdminStates.segment_selection)
        await callback.message.answer(
            "Выберите параметр для сегментации аудитории:",
            reply_markup=get_segment_keyboard()
        )
    else:
        # Если обычная рассылка, возвращаемся в главное меню
        await state.set_state(AdminStates.main_menu)
        await callback.message.answer(
            "Вы вернулись в главное меню админ-панели.",
            reply_markup=get_admin_main_keyboard()
        )

@admin_router.message(AdminStates.main_menu, F.text == "❌ Выход из админ-панели")
async def admin_exit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    await message.answer(
        "Вы вышли из админ-панели.",
        reply_markup=ReplyKeyboardRemove(),
        
    )
    
@admin_router.message(AdminStates.main_menu, F.text == "🗑 Удалить пользователя")
async def admin_delete_user_request(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_for_user_id)
    await message.answer(
        "Введите ID пользователя, которого нужно удалить:",
        reply_markup=get_admin_back_keyboard()
    )

@admin_router.message(AdminStates.waiting_for_user_id, F.text == "⬅️ Назад")
async def admin_delete_user_back(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.main_menu)
    await message.answer(
        "Вы вернулись в главное меню админ-панели.",
        reply_markup=get_admin_main_keyboard()
    )

@admin_router.message(AdminStates.waiting_for_user_id)
async def admin_delete_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text)
        deleted = await delete_user(user_id)
        
        if deleted:
            await message.answer(
                f"✅ Пользователь с ID {user_id} успешно удален из базы данных.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ Пользователь с ID {user_id} не найден в базе данных.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.set_state(AdminStates.main_menu)
    except ValueError:
        await message.answer(
            "❌ Ошибка: ID пользователя должен быть числом. Попробуйте снова.",
            reply_markup=get_admin_back_keyboard()
        )

@admin_router.message(Command(commands=['test_manager']))
async def cmd_test_manager(message: Message):
    """Тестовая команда для проверки отправки сообщений менеджеру"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        await message.bot.send_message(
            chat_id=settings.MANAGER_CHAT_ID,
            text="Это тестовое сообщение для проверки отправки уведомлений менеджеру."
        )
        await message.answer("Тестовое сообщение успешно отправлено менеджеру.")
    except Exception as e:
        await message.answer(f"Ошибка при отправке тестового сообщения: {e}")