import asyncio
import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.common import common_router
from handlers.rating import rating_router
from database.create_tables import create_tables
from handlers.onboarding import onboarding_router 
from handlers.admin import admin_router
from config.settings import settings
from services.session_analyzer import start_session_analyzer, add_message_to_session

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем токен из переменных окружения
TG_TOKEN = os.getenv('TG_TOKEN')

async def main():
    try:
        # Создаем таблицы в базе данных
        await create_tables()
        
        # Создаем хранилище состояний для FSM
        storage = MemoryStorage()
        
        # Создаем экземпляры бота и диспетчера
        bot = Bot(token=TG_TOKEN)
        dp = Dispatcher(storage=storage)
        
        logger.info('Starting bot...')
        
        # Регистрируем роутеры
        dp.include_router(admin_router)
        dp.include_router(onboarding_router)
        dp.include_router(common_router)
        dp.include_router(rating_router)
        
        # Запускаем анализатор сессий в отдельной задаче
        asyncio.create_task(start_session_analyzer(bot))
        logger.info('Session analyzer started')
        
        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as ex:
        logger.error(f'Error starting bot: {ex}', exc_info=True)
    finally:
        # Закрываем сессию бота при выходе
        if 'bot' in locals():
            await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot stopped')
