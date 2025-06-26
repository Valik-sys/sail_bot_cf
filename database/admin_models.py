from database.database import get_db_connection

async def get_users_count():
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT COUNT(*) FROM users')
            result = await cursor.fetchone()
            return result[0] if result else 0
    finally:
        await conn.close()


async def get_messages_count():
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT COUNT(*) FROM messages')
            result = await cursor.fetchone()
            return result[0] if result else 0
    finally:
        await conn.close()
        

async def get_ratings_stats():
    """Возвращает статистику по оценкам"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Общее количество оценок
            await cursor.execute('SELECT COUNT(*) FROM ratings')
            total_count = await cursor.fetchone()
            
            # Средняя оценка
            await cursor.execute('SELECT AVG(rating) FROM ratings')
            avg_rating = await cursor.fetchone()
            
            # Распределение оценок
            await cursor.execute('SELECT rating, COUNT(*) FROM ratings GROUP BY rating ORDER BY rating')
            distribution = await cursor.fetchall()
            
            return {
                "total_count": total_count[0] if total_count else 0,
                "avg_rating": round(avg_rating[0], 2) if avg_rating and avg_rating[0] else 0,
                "distribution": {row[0]: row[1] for row in distribution} if distribution else {}
            }
    finally:
        await conn.close()
        
async def get_all_users():
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT user_id, username, first_name, last_name, time_added FROM users ORDER BY time_added DESC')
            users = await cursor.fetchall()
            return users
    finally:
        await conn.close()
        
async def get_all_user_ids():
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT user_id FROM users')
            user_ids = await cursor.fetchall()
            return [row[0] for row in user_ids]
    finally:
        await conn.close()
        
async def get_users_by_segment(country=None, interests=None, subject=None):
    """Получает список пользователей по сегментам"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            query = 'SELECT user_id FROM users WHERE 1=1'
            params = []
            
            if country:
                query += ' AND country = ?'
                params.append(country)
                
            if interests:
                query += ' AND interests LIKE ?'
                params.append(f'%{interests}%')
                
            if subject:
                query += ' AND subject = ?'
                params.append(subject)
                
            await cursor.execute(query, params)
            user_ids = await cursor.fetchall()
            return [row[0] for row in user_ids]
    finally:
        await conn.close()
        
async def get_available_segments():
    """Получает доступные сегменты для фильтрации"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Получаем уникальные страны
            await cursor.execute('SELECT DISTINCT country FROM users WHERE country IS NOT NULL')
            countries = await cursor.fetchall()
            
            # Получаем уникальные предметы
            await cursor.execute('SELECT DISTINCT subject FROM users WHERE subject IS NOT NULL')
            subjects = await cursor.fetchall()
            
            # Для интересов нужно обработать, так как они могут быть в одном поле через запятую
            await cursor.execute('SELECT DISTINCT interests FROM users WHERE interests IS NOT NULL')
            interests_raw = await cursor.fetchall()
            
            # Обрабатываем интересы, разделяя их, если они записаны через запятую
            interests_set = set()
            for interest_row in interests_raw:
                if interest_row[0]:
                    for interest in interest_row[0].split(','):
                        interests_set.add(interest.strip())
            
            return {
                "countries": [row[0] for row in countries],
                "subjects": [row[0] for row in subjects],
                "interests": list(interests_set)
            }
    finally:
        await conn.close()
        
async def get_users_by_segment(country=None, interests=None, subject=None):
    """Получает список пользователей по сегментам"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            query = 'SELECT user_id FROM users WHERE 1=1'
            params = []
            
            if country:
                query += ' AND country = ?'
                params.append(country)
                
            if interests:
                query += ' AND interests LIKE ?'
                params.append(f'%{interests}%')
                
            if subject:
                query += ' AND subject = ?'
                params.append(subject)
                
            await cursor.execute(query, params)
            user_ids = await cursor.fetchall()
            return [row[0] for row in user_ids]
    finally:
        await conn.close()
        
async def delete_user(user_id):
    """Удаляет пользователя из базы данных по его user_id"""
    conn = await get_db_connection()
    try:
        async with conn.cursor() as cursor:
            # Сначала удаляем связанные записи из таблицы ratings
            await cursor.execute('''
                DELETE FROM ratings WHERE user_id = ?
            ''', (user_id,))
            
            # Затем удаляем связанные записи из таблицы messages
            await cursor.execute('''
                DELETE FROM messages WHERE user_id = ?
            ''', (user_id,))
            
            # Наконец, удаляем самого пользователя
            await cursor.execute('''
                DELETE FROM users WHERE user_id = ?
            ''', (user_id,))
            
            await conn.commit()
            
            # Возвращаем количество удаленных строк
            return cursor.rowcount
    except Exception as e:
        print(f"Ошибка при удалении пользователя: {e}")
        return 0
    finally:
        await conn.close()
