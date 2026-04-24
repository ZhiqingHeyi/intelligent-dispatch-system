import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_DB = {
    'cable_car': {
        'host': '192.168.1.88',
        'port': 3306,
        'user': 'root',
        'password': '!Tmhc20170717',
        'database': 'cable_car',
        'charset': 'utf8mb4'
    },
    'vehicle_system': {
        'host': '192.168.1.88',
        'port': 3306,
        'user': 'root',
        'password': '!Tmhc20170717',
        'database': 'vehicle_system',
        'charset': 'utf8mb4'
    }
}

LOCAL_DB = os.path.join(BASE_DIR, 'dispatch.db')

SYNC_INTERVAL = 3

CONCRETE_GRADES = [
    '二级配',
    '三级配',
    '四级配',
    '三级配PVA纤维',
    '三级富浆'
]

CABLE_CAR_RETURN_THRESHOLD = -0.5
VEHICLE_GOING_THRESHOLD = -10
