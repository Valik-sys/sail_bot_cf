from datetime import datetime
from database.database import get_db_connection

# Функции для работы с пользователями
async def add_user(user_id, username, first_name, last_name):
    """Добавляет нового пользователя в базу данных"""
    time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, time_added)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, time_added))
            await conn.commit()
    finally:
        await conn.close()

async def get_user(user_id):
    """Получает информацию о пользователе по его ID"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return await cursor.fetchone()
    finally:
        await conn.close()

# Функции для работы с сообщениями
async def add_message(user_id, message_text, response_text):
    """Добавляет новое сообщение в базу данных и возвращает его ID"""
    time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO messages (user_id, message_text, response_text, time_added)
                VALUES (?, ?, ?, ?)
            ''', (user_id, message_text, response_text, time_added))
            await conn.commit()
            
            # Получаем ID последней вставленной записи
            await cursor.execute('SELECT last_insert_rowid()')
            result = await cursor.fetchone()
            return result[0] if result else None
    finally:
        await conn.close()

# Функции для работы с оценками
async def add_rating(message_id, user_id, rating, feedback=None):
    """Добавляет или обновляет оценку сообщения"""
    time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Вызов add_rating: message_id={message_id}, user_id={user_id}, rating={rating}, feedback={feedback}")
    
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Проверяем, существует ли уже оценка для этого сообщения
            await cursor.execute('''
                SELECT id FROM ratings WHERE message_id = ? AND user_id = ?
            ''', (message_id, user_id))
            
            existing_rating = await cursor.fetchone()
            
            if existing_rating:
                # Обновляем существующую оценку
                print(f"Обновляем существующую оценку с id={existing_rating[0]}")
                await cursor.execute('''
                    UPDATE ratings 
                    SET rating = ?, feedback = ?, time_added = ?
                    WHERE id = ?
                ''', (rating, feedback, time_added, existing_rating[0]))
            else:
                # Добавляем новую оценку
                print(f"Добавляем новую оценку")
                await cursor.execute('''
                    INSERT INTO ratings (message_id, user_id, rating, feedback, time_added)
                    VALUES (?, ?, ?, ?, ?)
                ''', (message_id, user_id, rating, feedback, time_added))
            
            await conn.commit()
            print("Транзакция успешно завершена")
    except Exception as e:
        print(f"Ошибка в add_rating: {e}")
        raise
    finally:
        await conn.close()
        
async def update_user_onboarding(user_id, country=None, interests=None,subject=None, completed=False):
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Формируем части запроса в зависимости от переданных параметров
            update_parts = []
            params = []
            
            if country is not None:
                update_parts.append("country = ?")
                params.append(country)
            
            if interests is not None:
                update_parts.append("interests = ?")
                params.append(interests)
                
            if subject is not None:
                update_parts.append("subject = ?")
                params.append(subject)  
                
            if completed:
                update_parts.append("onboarding_completed = TRUE")
                
            if update_parts:
                query = f"UPDATE users SET {', '.join(update_parts)} WHERE user_id = ?"
                params.append(user_id)
                await cursor.execute(query, params)
                await conn.commit()
                return True
            return False
    finally:
        await conn.close()
        
async def get_user_onboarding_status(user_id):
    # Проверяет, что пользователь завершил онбординг
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT onboarding_completed FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else False
    finally:
        await conn.close()

async def update_user_onboarding(user_id, country=None, interests=None, subject=None, completed=False):
    """Обновляет информацию о пользователе после онбординга"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Формируем части запроса в зависимости от переданных параметров
            update_parts = []
            params = []
            
            if country is not None:
                update_parts.append("country = ?")
                params.append(country)
                
            if interests is not None:
                update_parts.append("interests = ?")
                params.append(interests)
                
            if subject is not None:
                update_parts.append("subject = ?")
                params.append(subject)
                
            if completed:
                update_parts.append("onboarding_completed = 1")
            
            if update_parts:
                query = f"UPDATE users SET {', '.join(update_parts)} WHERE user_id = ?"
                params.append(user_id)
                await cursor.execute(query, params)
                await conn.commit()
                return True
            return False
    finally:
        await conn.close()

async def get_user_onboarding_status(user_id):
    """Проверяет, завершил ли пользователь онбординг"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT onboarding_completed FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            return bool(result[0]) if result else False
    finally:
        await conn.close()
