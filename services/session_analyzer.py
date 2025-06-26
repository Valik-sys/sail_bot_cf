import asyncio
import time
import logging
from datetime import datetime
from openai import AsyncOpenAI
from config.settings import settings
from database.models import get_user

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Словарь для хранения активных сессий
# Структура: {user_id: {'messages': [], 'last_activity': timestamp, 'analyzed': False}}
active_sessions = {}

# Таймаут сессии в секундах (10 минут)
SESSION_TIMEOUT = 15

async def add_message_to_session(user_id, user_message, bot_response):
    """Добавляет сообщение в сессию пользователя"""
    current_time = time.time()
    
    # Если у пользователя нет активной сессии или она истекла, создаем новую
    if user_id not in active_sessions or (current_time - active_sessions[user_id]['last_activity']) > SESSION_TIMEOUT:
        active_sessions[user_id] = {
            'messages': [],
            'last_activity': current_time,
            'analyzed': False
        }
    
    # Добавляем сообщение в сессию
    active_sessions[user_id]['messages'].append({
        'user': user_message,
        'bot': bot_response,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Обновляем время последней активности
    active_sessions[user_id]['last_activity'] = current_time
    logger.debug(f"Сообщение добавлено в сессию пользователя {user_id}")

async def analyze_session(user_id):
    """Анализирует сессию диалога и определяет потребности пользователя"""
    if user_id not in active_sessions or active_sessions[user_id]['analyzed']:
        return None
    
    session = active_sessions[user_id]
    messages = session['messages']
    
    if not messages or len(messages) < 1:  # Если меньше 2 сообщений, анализировать нечего
        session['analyzed'] = True
        return None
    
    # Формируем диалог для анализа
    dialog_text = ""
    for i, msg in enumerate(messages):
        dialog_text += f"Пользователь [{msg['time']}]: {msg['user']}\n"
        dialog_text += f"Бот: {msg['bot']}\n\n"
    
    # Формируем промпт для GPT
    prompt = f"""Проанализируй следующий диалог между пользователем и ботом. 
    
    Определи:
    1. Интересуется ли пользователь покупкой курса или каким то другим продуктом? Если да, то каким?
    2. Какие конкретные вопросы задавал пользователь?
    3. На какой стадии принятия решения находится пользователь?
    4. Что могло бы помочь пользователю принять решение о покупке?
    
    Дай краткий анализ (до 5 предложений) для менеджера по продажам.
    Если пользователь не проявляет интереса к покупке курса, просто напиши "Нет интереса к покупке курса".
    
    ДИАЛОГ:
    {dialog_text}
    """
    
    try:
        # Отправляем запрос к GPT
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": '''Ты - аналитик диалогов,
                 который определяет потребности клиентов и их интерес к покупке курсов и других продуктов.
                 Ты работаешь с диалогом между пользователем и ботом.
                 Твоя задача - дать краткий анализ диалога, выявить интересы пользователя'''},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        analysis_text = response.choices[0].message.content.strip()
        
        # Определяем, является ли пользователь потенциальным клиентом
        is_lead = "нет интереса к покупке курса" not in analysis_text.lower()
        
        # Отмечаем сессию как проанализированную
        session['analyzed'] = True
        
        if is_lead:
            logger.info(f"Пользователь {user_id} определен как потенциальный клиент")
            return {
                "user_id": user_id,
                "analysis_text": analysis_text,
                "is_lead": is_lead
            }
        logger.info(f"Пользователь {user_id} не проявляет интереса к покупке")
        return None
    except Exception as e:
        logger.error(f"Ошибка при анализе сессии для пользователя {user_id}: {e}", exc_info=True)
        session['analyzed'] = True  # Отмечаем как проанализированную, чтобы не пытаться снова
        return None

async def format_lead_message(analysis_result):
    """Форматирует сообщение о потенциальном клиенте для менеджера"""
    user_id = analysis_result["user_id"]
    user_data = await get_user(user_id)
    
    if not user_data:
        logger.warning(f"Не удалось получить данные пользователя {user_id}")
        return None
    
    username = user_data[2] or "Нет username"
    first_name = user_data[3] or ""
    last_name = user_data[4] or ""
    country = user_data[5] or "Не указана"
    interests = user_data[6] or "Не указаны"
    subject = user_data[7] or "Не указан"
    
    # Форматируем сообщение
    message = f"""🔍 НОВЫЙ ПОТЕНЦИАЛЬНЫЙ КЛИЕНТ

👤 Пользователь: @{username} ({first_name} {last_name})
📱 ID: {user_id}
🌍 Страна: {country}
📚 Предмет: {subject}
🔎 Интересы: {interests}

💬 АНАЛИЗ ДИАЛОГА:
{analysis_result["analysis_text"]}

⏰ Время анализа: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    return message

async def send_message_to_manager(bot, text):
    """Отправляет сообщение в группу менеджеров с обработкой ошибок"""
    try:
        await bot.send_message(
            chat_id=settings.MANAGER_CHAT_ID,
            text=text
        )
        logger.info(f"Сообщение успешно отправлено в группу менеджеров")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в группу менеджеров: {e}", exc_info=True)
        # Можно добавить уведомление администратора о проблеме
        try:
            await bot.send_message(
                chat_id=settings.ADMIN_ID,
                text=f"❌ Ошибка при отправке сообщения в группу менеджеров: {e}\n\nПроверьте настройки бота и группы."
            )
        except Exception as ex:
            logger.error(f"Не удалось отправить уведомление администратору: {ex}")
        return False

async def cleanup_sessions():
    """Удаляет проанализированные и устаревшие сессии из памяти"""
    current_time = time.time()
    users_to_remove = []
    
    for user_id, session in active_sessions.items():
        # Удаляем проанализированные сессии
        if session['analyzed']:
            users_to_remove.append(user_id)
        # Удаляем очень старые сессии (более 24 часов)
        elif (current_time - session['last_activity']) > 86400:  # 24 часа
            users_to_remove.append(user_id)
    
    # Удаляем сессии из словаря
    for user_id in users_to_remove:
        if user_id in active_sessions:
            del active_sessions[user_id]
    
    if users_to_remove:
        logger.info(f"Очищено {len(users_to_remove)} сессий из памяти")

async def check_inactive_sessions(bot):
    """Проверяет неактивные сессии и анализирует их"""
    current_time = time.time()
    
    for user_id, session in list(active_sessions.items()):
        try:
            # Если сессия неактивна более указанного таймаута и не проанализирована
            if (current_time - session['last_activity']) > SESSION_TIMEOUT and not session['analyzed']:
                logger.info(f"Обнаружена неактивная сессия пользователя {user_id}, начинаем анализ")
                # Анализируем сессию
                analysis_result = await analyze_session(user_id)
                
                if analysis_result and analysis_result["is_lead"]:
                    # Если это потенциальный клиент, форматируем сообщение для менеджера
                    lead_message = await format_lead_message(analysis_result)
                    
                    if lead_message:
                        # Отправляем сообщение менеджеру
                        await send_message_to_manager(bot, lead_message)
        except Exception as e:
            logger.error(f"Ошибка при обработке сессии пользователя {user_id}: {e}", exc_info=True)
            # Отмечаем сессию как проанализированную, чтобы не пытаться снова
            session['analyzed'] = True

async def start_session_analyzer(bot):
    """Запускает периодическую проверку неактивных сессий"""
    logger.info("Запущен анализатор сессий")
    while True:
        try:
            await check_inactive_sessions(bot)
            await cleanup_sessions()  # Очищаем проанализированные и устаревшие сессии
        except Exception as e:
            logger.error(f"Ошибка в цикле анализа сессий: {e}", exc_info=True)
        
        # Проверяем каждую минуту
        await asyncio.sleep(60)

