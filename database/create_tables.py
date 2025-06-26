from database.database import get_db_connection

async def create_tables():
    """Создает все необходимые таблицы в базе данных"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Таблица пользователей
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    country TEXT,
                    interests TEXT,
                    subject TEXT,
                    onboarding_completed BOOLEAN DEFAULT 0,
                    time_added TEXT
                )
            ''')
            
            # Таблица сообщений
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message_text TEXT,
                    response_text TEXT,
                    time_added TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица оценок
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS ratings(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER,
                    feedback TEXT,
                    time_added TEXT,
                    FOREIGN KEY (message_id) REFERENCES messages(id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
                        # Таблица сессий диалогов
    finally:
        await conn.close()

async def update_database_schema(cursor, conn):
    """Обновляет схему базы данных, добавляя новые столбцы, если их нет"""
    try:
        # Получаем информацию о столбцах таблицы users
        await cursor.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Проверяем и добавляем новые столбцы
        new_columns = {
            "country": "TEXT",
            "interests": "TEXT",
            "subject": "TEXT",
            "onboarding_completed": "BOOLEAN DEFAULT 0"
        }
        for column_name, column_type in new_columns.items():
            if column_name not in column_names:
                print(f"Добавление столбца {column_name} в таблицу users")
                await cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
        
        await conn.commit()
        print("Схема базы данных успешно обновлена")
    except Exception as e:
        print(f"Ошибка при обновлении схемы базы данных: {e}")
        raise
