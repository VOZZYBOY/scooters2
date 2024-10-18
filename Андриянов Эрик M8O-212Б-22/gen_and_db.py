import psycopg2
import random

# Параметры подключения к базе данных PostgreSQL
db_params = {
    'host': '176.97.77.28',  # IP-адрес сервера, если он удалённый
    'database': 'scoot',
    'user': 'myuser',
    'password': 'mypassword',
    'port': '5432'
}

# Функция для генерации случайных данных и сохранения их в базу PostgreSQL
def generate_and_save_data(num_scooters, num_stations):
    try:
        # Устанавливаем соединение с базой данных
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Генерируем и сохраняем данные для самокатов
        for _ in range(num_scooters):
            x = random.uniform(-90, 90)
            y = random.uniform(-180, 180)
            charge = random.randint(0, 100)  # Генерация случайного заряда от 0 до 100%
            cursor.execute('''
                INSERT INTO scooters (x, y, charge) VALUES (%s, %s, %s)
            ''', (x, y, charge))

        # Генерируем и сохраняем данные для зарядных станций
        for _ in range(num_stations):
            x = random.uniform(-90, 90)
            y = random.uniform(-180, 180)
            cursor.execute('''
                INSERT INTO charging_stations (x, y) VALUES (%s, %s)
            ''', (x, y))

        conn.commit()
        print("Данные успешно сгенерированы и сохранены в базу данных PostgreSQL.")
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}")
    finally:
        if conn is not None:
            conn.close()

# Вызов функции для генерации 150 самокатов и 10 зарядных станций