import math
import random
import psycopg2
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.lines import Line2D

TIME_LIMIT = 2000

# Параметры подключения к базе данных
db_params = {
    'host': '176.97.77.28',
    'database': 'scoot',
    'user': 'myuser',
    'password': 'mypassword',
    'port': '5432'
}

class Scooter:
    def __init__(self, id, x, y, charge):
        self.id = id
        self.x = x
        self.y = y
        self.charge = charge
        self.reserved = False

    def __repr__(self):
        return f"Scooter {self.id} at ({self.x}, {self.y}) with {self.charge}% charge"

class ChargingStation:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.charged_accums = 10
        self.discharged_accums = 0
        self.visited = False

    def __repr__(self):
        return f"Charging station {self.id} at ({self.x}, {self.y})"

# Подключение к базе данных
def connect_db():
    try:
        return psycopg2.connect(**db_params)
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

# Получение данных о самокатах
def load_scooters(conn, limit=150):
    scooters = []
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT id, x, y, charge FROM scooters LIMIT {limit}")
            scooters = [Scooter(*row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error fetching scooters: {e}")
    return scooters

# Получение данных о зарядных станциях
def load_charging_stations(conn, limit=20):
    stations = []
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT id, x, y FROM charging_stations LIMIT {limit}")
            stations = [ChargingStation(*row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error fetching charging stations: {e}")
    return stations

# Функция для визуализации объектов
def plot_data(ax, scooters, stations, current_pos=None, next_scooter=None):
    ax.clear()
    ax.set_facecolor('#f5f5f5')

    # Отрисовка зарядных станций (зелёные звезды)
    for station in stations:
        ax.plot(station.x, station.y, 'g*', markersize=10)

    # Отрисовка самокатов
    for scooter in scooters:
        if scooter.charge < 50:
            ax.plot(scooter.x, scooter.y, 'bD', markersize=8)
        else:
            ax.plot(scooter.x, scooter.y, 'ms', markersize=8)

    # Отрисовка текущей позиции чарджера
    if current_pos:
        ax.plot(current_pos[0], current_pos[1], 'ro', markersize=15)

   # Отрисовка следующего самоката
   # Отрисовка следующего самоката
    if next_scooter:
        ax.plot(next_scooter.x, next_scooter.y, 'h', color='green', markersize=10, label='Next Scooter')  # Зеленый шестиугольник



    # Вычисление среднего заряда
    avg_charge = sum(s.charge for s in scooters) / len(scooters) if scooters else 0
    ax.text(0.95, 0.9, f'Avg charge: {avg_charge:.2f}%', transform=ax.transAxes,
            fontsize=16, fontweight='bold', color='darkgreen', ha='right')

    # Легенда
    legend_elements = [
        Line2D([0], [0], marker='D', color='w', label='< 50% charge', markerfacecolor='blue', markersize=8),
        Line2D([0], [0], marker='s', color='w', label='>= 50% charge', markerfacecolor='magenta', markersize=8),
        Line2D([0], [0], marker='*', color='w', label='Charging station', markerfacecolor='green', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Charger', markerfacecolor='red', markersize=15),
        Line2D([0], [0], marker='h', color='w', label='Next scooter', markerfacecolor='pink', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))

    plt.draw()

# Вычисление расстояния между двумя точками
def calculate_distance(p1, p2):
    x1, y1 = (p1.x, p1.y) if isinstance(p1, Scooter) else p1
    x2, y2 = (p2.x, p2.y) if isinstance(p2, Scooter) else p2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Нахождение ближайшей зарядной станции
def find_nearest_station(position, stations):
    unvisited = [s for s in stations if not s.visited]
    return min(unvisited, key=lambda s: calculate_distance(position, (s.x, s.y)))

# Нахождение ближайших самокатов
def find_nearest_scooters(position, scooters, count=10):
    available = [s for s in scooters if not s.reserved and s.charge < 50]
    available.sort(key=lambda s: calculate_distance(position, (s.x, s.y)))
    return available[:count]

# Случайное перемещение самокатов
def move_scooters(scooters, max_move=10):
    for scooter in random.sample([s for s in scooters if not s.reserved], min(10, len(scooters))):
        scooter.x += random.uniform(-max_move, max_move)
        scooter.y += random.uniform(-max_move, max_move)
        scooter.charge = max(0, scooter.charge - calculate_distance((scooter.x, scooter.y), (scooter.x, scooter.y)) * 0.1)

# Следующий шаг симуляции
def next_step(event):
    global charger_position, scooters, stations, charger_accums, total_distance

    if total_distance >= TIME_LIMIT:
        print("Time limit reached")
        return

    move_scooters(scooters)
    next_scooter = find_nearest_scooters(charger_position, scooters)[0]
    distance = calculate_distance(charger_position, (next_scooter.x, next_scooter.y))

    if total_distance + distance <= TIME_LIMIT:
        charger_position = (next_scooter.x, next_scooter.y)
        total_distance += distance
        next_scooter.charge = 100
        next_scooter.reserved = True
        charger_accums -= 1

    plot_data(ax, scooters, stations, charger_position, next_scooter)

# Конец симуляции
def end_simulation(event):
    print("End of simulation.")
    plot_data(ax, scooters, stations, charger_position)

# Основная программа
conn = connect_db()
if conn:
    scooters = load_scooters(conn)
    stations = load_charging_stations(conn)
    charger_position = (float(input("Enter X for charger: ")), float(input("Enter Y for charger: ")))
    charger_accums = 10
    total_distance = 0

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    btn_next = Button(plt.axes([0.81, 0.05, 0.1, 0.075]), 'Next', color='lightblue', hovercolor='blue')
    btn_next.on_clicked(next_step)
    btn_end = Button(plt.axes([0.7, 0.05, 0.1, 0.075]), 'End', color='lightgreen', hovercolor='green')
    btn_end.on_clicked(end_simulation)

    plot_data(ax, scooters, stations, charger_position)
    plt.show()
else:
    print("Failed to connect to the database.")
