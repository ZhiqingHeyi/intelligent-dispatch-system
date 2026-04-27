import json
import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from database import init_db, get_db, update_cable_car_grade, update_cable_car_state, update_vehicle_grade, create_dispatch_task, complete_dispatch_task, cancel_dispatch_task
from data_sync import sync_all, start_sync_loop, stop_sync_loop
from config import CONCRETE_GRADES

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
app.debug = True

VUE_DIST_DIR = os.path.join(app.static_folder, 'vue-dist')
VUE_ASSETS_DIR = os.path.join(VUE_DIST_DIR, 'assets')


def _get_vue_assets():
    js_file = ''
    css_file = ''
    if os.path.isdir(VUE_ASSETS_DIR):
        for f in os.listdir(VUE_ASSETS_DIR):
            if f.endswith('.js') and f.startswith('index'):
                js_file = f
            elif f.endswith('.css') and f.startswith('index'):
                css_file = f
    return js_file, css_file


init_db()

@app.route('/')
def index():
    js_file, css_file = _get_vue_assets()
    return render_template('index.html', js_file=js_file, css_file=css_file)

@app.route('/static/vue-dist/assets/<path:filename>')
def vue_assets(filename):
    return send_from_directory(VUE_ASSETS_DIR, filename)

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


# ==================== AI 智能调度 API ====================

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    try:
        from ai_engine import chat_with_ai
        from ai_experience import get_all_ai_config
        config = get_all_ai_config()
        if not config.get('api_key'):
            return jsonify({
                'response': '⚠️ AI模型未配置。请点击右下角🤖按钮 → ⚙设置，配置API Key后再试。',
                'tool_results': [],
                'success': False,
                'error_type': 'config_missing'
            })
        if not config.get('api_url'):
            return jsonify({
                'response': '⚠️ API地址未配置。请在设置中填写正确的API地址。',
                'tool_results': [],
                'success': False,
                'error_type': 'config_missing'
            })
        if not config.get('model'):
            return jsonify({
                'response': '⚠️ 模型名称未配置。请在设置中填写模型名称（如gpt-4o、deepseek-chat等）。',
                'tool_results': [],
                'success': False,
                'error_type': 'config_missing'
            })
        data = request.json or {}
        message = data.get('message', '')
        result = chat_with_ai(message)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'response': f'⚠️ AI服务异常: {str(e)}。请检查AI模型配置是否正确。',
            'tool_results': [],
            'success': False,
            'error_type': 'service_error'
        }), 500

@app.route('/api/ai/dispatch', methods=['POST'])
def ai_dispatch():
    try:
        from ai_engine import ai_auto_dispatch
        from ai_experience import get_all_ai_config
        config = get_all_ai_config()
        if not config.get('api_key'):
            return jsonify({
                'response': '⚠️ 无法执行智能调度：AI模型未配置。请先点击右下角🤖按钮 → ⚙设置，完成API配置。',
                'tool_results': [],
                'success': False,
                'error_type': 'config_missing'
            })
        if not config.get('api_url') or not config.get('model'):
            return jsonify({
                'response': '⚠️ AI配置不完整（缺少API地址或模型名称），请先完成配置。',
                'tool_results': [],
                'success': False,
                'error_type': 'config_missing'
            })
        result = ai_auto_dispatch()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'response': f'⚠️ AI调度执行失败: {str(e)}。请检查网络连接和AI模型配置。',
            'tool_results': [],
            'success': False,
            'error_type': 'service_error'
        }), 500

@app.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    try:
        from ai_experience import get_all_ai_config
        config = get_all_ai_config()
        masked_config = dict(config)
        if masked_config.get('api_key'):
            key = masked_config['api_key']
            masked_config['api_key'] = key[:8] + '***' + key[-4:] if len(key) > 12 else '***'
            masked_config['api_key_configured'] = True
        else:
            masked_config['api_key_configured'] = False
        return jsonify({'success': True, 'config': masked_config})
    except Exception as e:
        return jsonify({'success': False, 'message': f'读取配置失败: {str(e)}'}), 500

@app.route('/api/ai/config', methods=['POST'])
def save_ai_config():
    try:
        from ai_experience import save_all_ai_config, get_all_ai_config, validate_ai_config
        data = request.json or {}

        api_key_raw = data.get('api_key', '')
        if api_key_raw and '***' in api_key_raw:
            data = {k: v for k, v in data.items() if k != 'api_key'}

        if 'api_key' not in data:
            current_config = get_all_ai_config()
            data['api_key'] = current_config.get('api_key', '')

        errors = validate_ai_config(data)
        if errors:
            return jsonify({'success': False, 'message': '配置验证失败: ' + '; '.join(errors), 'errors': errors}), 400

        data['enabled'] = bool(data.get('api_key'))

        save_all_ai_config(data)

        saved = get_all_ai_config()
        verify_ok = bool(saved.get('api_key')) and bool(saved.get('api_url')) and bool(saved.get('model'))

        return jsonify({
            'success': True,
            'message': '配置已保存' + ('' if verify_ok else '，但部分配置可能未正确存储，请重新检查'),
            'verified': verify_ok
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存配置失败: {str(e)}'}), 500

@app.route('/api/ai/config/test', methods=['POST'])
def test_ai_config():
    try:
        from ai_experience import test_ai_connection, get_all_ai_config
        data = request.json or {}
        api_url = data.get('api_url', '').strip()
        api_key = data.get('api_key', '').strip()
        model = data.get('model', '').strip()

        if not api_key or '***' in api_key:
            current = get_all_ai_config()
            api_key = current.get('api_key', '')
        if not api_url:
            current = get_all_ai_config()
            api_url = current.get('api_url', '')
        if not model:
            current = get_all_ai_config()
            model = current.get('model', '')

        if not all([api_url, api_key, model]):
            return jsonify({'success': False, 'message': '缺少必要的配置参数(api_url/api_key/model)'})

        result = test_ai_connection(api_url, api_key, model)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'测试连接失败: {str(e)}'})

@app.route('/api/ai/scheduler', methods=['GET'])
def get_ai_scheduler():
    try:
        from ai_scheduler import get_scheduler_status
        status = get_scheduler_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai/scheduler/start', methods=['POST'])
def start_ai_scheduler():
    try:
        from ai_scheduler import start_ai_scheduler
        result = start_ai_scheduler()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai/scheduler/stop', methods=['POST'])
def stop_ai_scheduler():
    try:
        from ai_scheduler import stop_ai_scheduler
        result = stop_ai_scheduler()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai/chat/history', methods=['GET'])
def get_ai_chat_history():
    try:
        from ai_experience import get_chat_history
        limit = request.args.get('limit', 50, type=int)
        history = get_chat_history(limit=limit)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai/chat/history', methods=['DELETE'])
def clear_ai_chat_history():
    try:
        from ai_experience import clear_chat_history
        clear_chat_history()
        return jsonify({'success': True, 'message': '聊天记录已清除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai/experience', methods=['GET'])
def get_ai_experience():
    try:
        from ai_experience import get_experience, get_experience_summary
        grade_id = request.args.get('grade_id', None, type=int)
        outcome = request.args.get('outcome', 'all')
        limit = request.args.get('limit', 20, type=int)
        experiences = get_experience(grade_id=grade_id, outcome=outcome, limit=limit)
        summary = get_experience_summary()
        return jsonify({'success': True, 'experiences': experiences, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ai/experience/<int:exp_id>/outcome', methods=['POST'])
def update_experience_outcome(exp_id):
    try:
        from ai_experience import update_experience_outcome
        data = request.json or {}
        outcome = data.get('outcome', 'success')
        detail = data.get('detail', '')
        operator_override = data.get('operator_override', False)
        override_reason = data.get('override_reason', '')
        update_experience_outcome(exp_id, outcome, detail, operator_override, override_reason)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    init_db()
    start_sync_loop()
    try:
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    finally:
        stop_sync_loop()
