from flask import Flask, jsonify, request, render_template
from database import init_db, get_db
from data_sync import sync_all, start_sync_loop, stop_sync_loop
from matcher import (
    find_returning_cable_cars, find_going_vehicles,
    match_vehicle_to_cable_car, create_dispatch_task,
    complete_dispatch_task, cancel_dispatch_task,
    get_all_dispatch_tasks, get_dispatch_stats
)
import os

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cable_cars', methods=['GET'])
def get_cable_cars():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM cable_car_status ORDER BY cable_car_id')
    rows = c.fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM vehicle_status ORDER BY tid')
    rows = c.fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/cable_car/<int:cable_car_id>/grade', methods=['POST'])
def set_cable_car_grade(cable_car_id):
    grade = request.json.get('grade', '')
    db = get_db()
    c = db.cursor()
    c.execute('UPDATE cable_car_status SET grade = ? WHERE cable_car_id = ?', (grade, cable_car_id))
    db.commit()
    db.close()
    return jsonify({'success': True, 'cable_car_id': cable_car_id, 'grade': grade})

@app.route('/api/vehicle/<int:tid>/grade', methods=['POST'])
def set_vehicle_grade(tid):
    grade = request.json.get('grade', '')
    db = get_db()
    c = db.cursor()
    c.execute('UPDATE vehicle_status SET grade = ? WHERE tid = ?', (grade, tid))
    db.commit()
    db.close()
    return jsonify({'success': True, 'tid': tid, 'grade': grade})

@app.route('/api/match', methods=['GET'])
def auto_match():
    matches = match_vehicle_to_cable_car()
    return jsonify({'matches': matches})

@app.route('/api/dispatch', methods=['POST'])
def dispatch():
    data = request.json
    cable_car_id = data.get('cable_car_id')
    vehicle_tid = data.get('vehicle_tid')
    grade = data.get('grade', '')

    if not cable_car_id or not vehicle_tid:
        return jsonify({'success': False, 'msg': '参数不完整'}), 400

    result = create_dispatch_task(cable_car_id, vehicle_tid, grade)
    return jsonify({'success': result})

@app.route('/api/dispatch/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    result = complete_dispatch_task(task_id)
    return jsonify({'success': result})

@app.route('/api/dispatch/<int:task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    result = cancel_dispatch_task(task_id)
    return jsonify({'success': result})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = get_all_dispatch_tasks()
    return jsonify(tasks)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = get_dispatch_stats()
    return jsonify(stats)

@app.route('/api/grades', methods=['GET'])
def get_grades():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT * FROM grade_config ORDER BY id')
    rows = c.fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/sync', methods=['POST'])
def manual_sync():
    result = sync_all()
    return jsonify({'success': result})

@app.route('/api/sync/start', methods=['POST'])
def start_sync():
    start_sync_loop()
    return jsonify({'success': True})

@app.route('/api/sync/stop', methods=['POST'])
def stop_sync():
    stop_sync_loop()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    sync_all()
    start_sync_loop()
    app.run(host='0.0.0.0', port=5000, debug=False)
