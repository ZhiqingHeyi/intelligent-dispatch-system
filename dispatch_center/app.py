import json
from flask import Flask, render_template, jsonify, request
from database import init_db, get_db, update_cable_car_grade, update_cable_car_state, update_vehicle_grade, create_dispatch_task, complete_dispatch_task, cancel_dispatch_task
from data_sync import sync_all, start_sync_loop, stop_sync_loop
from config import CONCRETE_GRADES

app = Flask(__name__)
app.debug = True  # 启用调试模式，自动重载后端代码

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    db = get_db()
    cable_cars = [dict(row) for row in db.execute('SELECT * FROM cable_cars ORDER BY id').fetchall()]
    vehicles = [dict(row) for row in db.execute('SELECT * FROM vehicles ORDER BY tid').fetchall()]
    active_tasks = [dict(row) for row in db.execute(
        '''SELECT t.*, cc.name as cable_car_name, v.name as vehicle_name, gc.name as grade_name, gc.color as grade_color
           FROM dispatch_tasks t
           LEFT JOIN cable_cars cc ON t.cable_car_id = cc.id
           LEFT JOIN vehicles v ON t.vehicle_id = v.id
           LEFT JOIN grade_config gc ON t.grade_id = gc.id
           WHERE t.status IN ('assigned', 'pending')
           ORDER BY t.created_at DESC'''
    ).fetchall()]
    recent_tasks = [dict(row) for row in db.execute(
        '''SELECT t.*, cc.name as cable_car_name, v.name as vehicle_name, gc.name as grade_name, gc.color as grade_color
           FROM dispatch_tasks t
           LEFT JOIN cable_cars cc ON t.cable_car_id = cc.id
           LEFT JOIN vehicles v ON t.vehicle_id = v.id
           LEFT JOIN grade_config gc ON t.grade_id = gc.id
           WHERE t.status IN ('completed', 'cancelled')
           ORDER BY t.created_at DESC LIMIT 20'''
    ).fetchall()]
    db.close()

    return jsonify({
        'cable_cars': cable_cars,
        'vehicles': vehicles,
        'grades': CONCRETE_GRADES,
        'active_tasks': active_tasks,
        'recent_tasks': recent_tasks
    })

@app.route('/api/cable-car/<int:car_id>/grade', methods=['POST'])
def set_cable_car_grade(car_id):
    data = request.json
    grade_id = data.get('grade_id', 0)
    update_cable_car_grade(car_id, grade_id)
    return jsonify({'success': True})

@app.route('/api/cable-car/<int:car_id>/state', methods=['POST'])
def set_cable_car_state_api(car_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        manual_state = data.get('manual_state', 'normal')
        if not manual_state:
            return jsonify({'success': False, 'message': '状态值不能为空'}), 400
            
        update_cable_car_state(car_id, manual_state)
        return jsonify({'success': True, 'message': '状态更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/<int:vehicle_id>/grade', methods=['POST'])
def set_vehicle_grade(vehicle_id):
    data = request.json
    grade_id = data.get('grade_id', 0)
    update_vehicle_grade(vehicle_id, grade_id)
    return jsonify({'success': True})

@app.route('/api/dispatch', methods=['POST'])
def dispatch():
    data = request.json
    cable_car_id = data.get('cable_car_id')
    vehicle_id = data.get('vehicle_id')
    grade_id = data.get('grade_id')

    if not all([cable_car_id, vehicle_id, grade_id]):
        return jsonify({'success': False, 'message': '参数不完整'}), 400

    db = get_db()
    car = db.execute('SELECT * FROM cable_cars WHERE id = ?', (cable_car_id,)).fetchone()
    vehicle = db.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()

    if not car or not vehicle:
        db.close()
        return jsonify({'success': False, 'message': '缆机或车辆不存在'}), 404

    if car['grade_id'] != grade_id or vehicle['grade_id'] != grade_id:
        db.close()
        return jsonify({'success': False, 'message': '级配不匹配'}), 400

    existing = db.execute(
        'SELECT id FROM dispatch_tasks WHERE cable_car_id = ? AND status IN ("assigned","pending")',
        (cable_car_id,)
    ).fetchone()
    if existing:
        db.close()
        return jsonify({'success': False, 'message': '该缆机已有进行中的任务'}), 400

    existing_v = db.execute(
        'SELECT id FROM dispatch_tasks WHERE vehicle_id = ? AND status IN ("assigned","pending")',
        (vehicle_id,)
    ).fetchone()
    if existing_v:
        db.close()
        return jsonify({'success': False, 'message': '该车辆已有进行中的任务'}), 400

    db.close()
    task_id = create_dispatch_task(cable_car_id, vehicle_id, grade_id)
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/api/dispatch/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    complete_dispatch_task(task_id)
    return jsonify({'success': True})

@app.route('/api/dispatch/<int:task_id>/cancel', methods=['PUT'])
def cancel_task(task_id):
    cancel_dispatch_task(task_id)
    return jsonify({'success': True})

@app.route('/api/sync', methods=['POST'])
def manual_sync():
    result = sync_all()
    return jsonify({'success': result})

if __name__ == '__main__':
    init_db()
    start_sync_loop()
    try:
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    finally:
        stop_sync_loop()
