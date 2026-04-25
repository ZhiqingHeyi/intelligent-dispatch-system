import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'dispatch.db')

CABLE_CAR_DB = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'cable_car',
    'charset': 'utf8mb4'
}

VEHICLE_DB = {
    'host': '192.168.1.88',
    'port': 3306,
    'user': 'root',
    'password': '!Tmhc20170717',
    'database': 'vehicle_system',
    'charset': 'utf8mb4'
}

SYNC_INTERVAL = 3

CONCRETE_GRADES = [
    {'id': 1, 'name': '二级配', 'color': '#00d4ff'},
    {'id': 2, 'name': '三级配', 'color': '#00ff88'},
    {'id': 3, 'name': '四级配', 'color': '#ff6b6b'},
    {'id': 4, 'name': '三级配PVA纤维', 'color': '#ffd93d'},
    {'id': 5, 'name': '三级富浆', 'color': '#c084fc'},
]

CABLE_CAR_RETURN_THRESHOLD = -0.5
VEHICLE_GOING_THRESHOLD = -10
