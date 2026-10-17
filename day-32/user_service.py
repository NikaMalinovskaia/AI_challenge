# user_service.py
import sqlite3

def get_user_data(user_id):
    # БАГ: нет обработки ошибок, если user_id не передали или он None
    # АРХИТЕКТУРНЫЙ КОСЯК: прямой SQL-запрос внутри бизнес-логики без репозитория
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE id = {user_id}" # Уязвимость к SQL-инъекции тоже тут
    cursor.execute(query)
    result = cursor.fetchone()
    
    conn.close()
    return result
# Test PR changes for AI review
