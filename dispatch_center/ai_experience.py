import sqlite3
import json
from datetime import datetime
from database import get_db

GRADE_NAMES = {
    1: '二级配',
    2: '三级配',
    3: '四级配',
    4: '三级配PVA纤维',
    5: '三级富浆',
}

CONFIG_TYPE_MAP = {
    'api_url': str,
    'api_key': str,
    'model': str,
    'temperature': float,
    'max_tokens': int,
    'enabled': bool,
    'auto_dispatch_enabled': bool,
    'dispatch_interval': int,
}


def _coerce_config_value(key, value):
    target_type = CONFIG_TYPE_MAP.get(key)
    if target_type is None:
        return value
    if value is None:
        return value
    try:
        if target_type == bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        if target_type == int:
            return int(float(value))
        if target_type == float:
            return float(value)
        if target_type == str:
            return str(value)
    except (ValueError, TypeError):
        return value
    return value


def init_ai_tables():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS ai_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ai_chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        tool_calls TEXT,
        tool_result TEXT,
        created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ai_experience (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cable_car_id INTEGER NOT NULL,
        vehicle_id INTEGER NOT NULL,
        grade_id INTEGER NOT NULL,
        grade_name TEXT,
        cable_car_state TEXT,
        vehicle_state TEXT,
        cable_car_latitude REAL,
        vehicle_result_y REAL,
        ai_reasoning TEXT,
        outcome TEXT DEFAULT 'pending',
        outcome_detail TEXT,
        operator_override INTEGER DEFAULT 0,
        override_reason TEXT,
        created_at TEXT NOT NULL,
        resolved_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ai_dispatch_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        cable_car_id INTEGER NOT NULL,
        vehicle_id INTEGER NOT NULL,
        grade_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        reasoning TEXT,
        source TEXT DEFAULT 'ai',
        created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS ai_schedule_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT
    )''')

    conn.commit()
    conn.close()


def get_ai_config():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM ai_config').fetchall()
    conn.close()
    config = {}
    for row in rows:
        try:
            config[row['key']] = json.loads(row['value'])
        except (json.JSONDecodeError, TypeError):
            config[row['key']] = row['value']
    return config


def set_ai_config(key, value):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    coerced = _coerce_config_value(key, value)
    if isinstance(coerced, str):
        stored_value = coerced
    else:
        stored_value = json.dumps(coerced, ensure_ascii=False)
    conn.execute(
        'INSERT OR REPLACE INTO ai_config (key, value, updated_at) VALUES (?, ?, ?)',
        (key, stored_value, now)
    )
    conn.commit()
    conn.close()


def get_all_ai_config():
    from ai_config import AI_DEFAULT_CONFIG
    stored = get_ai_config()
    result = {}
    for key, default_val in AI_DEFAULT_CONFIG.items():
        raw = stored.get(key, default_val)
        result[key] = _coerce_config_value(key, raw)
    return result


def save_all_ai_config(config_dict):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        for key, value in config_dict.items():
            coerced = _coerce_config_value(key, value)
            if isinstance(coerced, str):
                stored_value = coerced
            else:
                stored_value = json.dumps(coerced, ensure_ascii=False)
            conn.execute(
                'INSERT OR REPLACE INTO ai_config (key, value, updated_at) VALUES (?, ?, ?)',
                (key, stored_value, now)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def validate_ai_config(config_dict):
    errors = []
    api_url = config_dict.get('api_url', '').strip() if config_dict.get('api_url') else ''
    api_key = config_dict.get('api_key', '').strip() if config_dict.get('api_key') else ''
    model = config_dict.get('model', '').strip() if config_dict.get('model') else ''

    if not api_url:
        errors.append('API地址不能为空')
    elif not api_url.startswith('http'):
        errors.append('API地址必须以http://或https://开头')

    if not api_key:
        errors.append('API Key不能为空')
    elif '***' in api_key:
        pass
    elif len(api_key) < 8:
        errors.append('API Key长度不足，请检查是否输入完整')

    if not model:
        errors.append('模型名称不能为空')

    try:
        temp = float(config_dict.get('temperature', 0.3))
        if not (0 <= temp <= 2):
            errors.append('Temperature应在0-2之间')
    except (ValueError, TypeError):
        errors.append('Temperature格式错误')

    try:
        max_tokens = int(float(config_dict.get('max_tokens', 2048)))
        if not (64 <= max_tokens <= 32768):
            errors.append('Max Tokens应在64-32768之间')
    except (ValueError, TypeError):
        errors.append('Max Tokens格式错误')

    return errors


def test_ai_connection(api_url, api_key, model):
    import requests
    try:
        resp = requests.post(
            api_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': '你好，请回复"连接成功"'}],
                'max_tokens': 20
            },
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            return {'success': True, 'message': f'连接成功，模型回复: {reply[:50]}'}
        elif resp.status_code == 401:
            return {'success': False, 'message': 'API Key无效(401)，请检查密钥是否正确'}
        elif resp.status_code == 404:
            return {'success': False, 'message': f'模型不存在(404)，请检查模型名称"{model}"是否正确'}
        elif resp.status_code == 429:
            return {'success': True, 'message': '连接正常但频率受限(429)，稍后可正常使用'}
        else:
            return {'success': False, 'message': f'服务返回错误({resp.status_code}): {resp.text[:200]}'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'message': f'无法连接到API地址，请检查地址是否正确: {api_url[:50]}'}
    except requests.exceptions.Timeout:
        return {'success': False, 'message': '连接超时，请检查网络或API地址是否可达'}
    except Exception as e:
        return {'success': False, 'message': f'连接测试失败: {str(e)}'}


def save_chat_message(role, content, tool_calls=None, tool_result=None):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'INSERT INTO ai_chat_history (role, content, tool_calls, tool_result, created_at) VALUES (?, ?, ?, ?, ?)',
        (role, content,
         json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
         json.dumps(tool_result, ensure_ascii=False) if tool_result else None,
         now)
    )
    conn.commit()
    conn.close()


def get_chat_history(limit=50):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM ai_chat_history ORDER BY id DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    messages = []
    for row in reversed(rows):
        msg = {
            'id': row['id'],
            'role': row['role'],
            'content': row['content'],
            'created_at': row['created_at']
        }
        if row['tool_calls']:
            msg['tool_calls'] = json.loads(row['tool_calls'])
        if row['tool_result']:
            msg['tool_result'] = json.loads(row['tool_result'])
        messages.append(msg)
    return messages


def clear_chat_history():
    conn = get_db()
    conn.execute('DELETE FROM ai_chat_history')
    conn.commit()
    conn.close()


def save_experience(cable_car_id, vehicle_id, grade_id, ai_reasoning,
                    cable_car_state='', vehicle_state='',
                    cable_car_latitude=0, vehicle_result_y=0):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    grade_name = GRADE_NAMES.get(grade_id, f'级配{grade_id}')
    conn.execute(
        '''INSERT INTO ai_experience
           (cable_car_id, vehicle_id, grade_id, grade_name,
            cable_car_state, vehicle_state, cable_car_latitude, vehicle_result_y,
            ai_reasoning, outcome, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)''',
        (cable_car_id, vehicle_id, grade_id, grade_name,
         cable_car_state, vehicle_state, cable_car_latitude, vehicle_result_y,
         ai_reasoning, now)
    )
    conn.commit()
    conn.close()


def update_experience_outcome(exp_id, outcome, detail='', operator_override=False, override_reason=''):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        '''UPDATE ai_experience
           SET outcome=?, outcome_detail=?, operator_override=?, override_reason=?, resolved_at=?
           WHERE id=?''',
        (outcome, detail, 1 if operator_override else 0, override_reason, now, exp_id)
    )
    conn.commit()
    conn.close()


def get_experience(grade_id=None, outcome='all', limit=10):
    conn = get_db()
    query = 'SELECT * FROM ai_experience WHERE 1=1'
    params = []
    if grade_id:
        query += ' AND grade_id = ?'
        params.append(grade_id)
    if outcome != 'all':
        query += ' AND outcome = ?'
        params.append(outcome)
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_experience_summary():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as cnt FROM ai_experience').fetchone()['cnt']
    success = conn.execute("SELECT COUNT(*) as cnt FROM ai_experience WHERE outcome='success'").fetchone()['cnt']
    failure = conn.execute("SELECT COUNT(*) as cnt FROM ai_experience WHERE outcome='failure'").fetchone()['cnt']
    pending = conn.execute("SELECT COUNT(*) as cnt FROM ai_experience WHERE outcome='pending'").fetchone()['cnt']
    overrides = conn.execute("SELECT COUNT(*) as cnt FROM ai_experience WHERE operator_override=1").fetchone()['cnt']
    conn.close()
    return {
        'total': total,
        'success': success,
        'failure': failure,
        'pending': pending,
        'overrides': overrides,
        'success_rate': round(success / total * 100, 1) if total > 0 else 0
    }


def save_dispatch_log(task_id, cable_car_id, vehicle_id, grade_id, action, reasoning='', source='ai'):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        '''INSERT INTO ai_dispatch_log
           (task_id, cable_car_id, vehicle_id, grade_id, action, reasoning, source, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (task_id, cable_car_id, vehicle_id, grade_id, action, reasoning, source, now)
    )
    conn.commit()
    conn.close()


def get_schedule_config():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM ai_schedule_config').fetchall()
    conn.close()
    config = {}
    for row in rows:
        try:
            config[row['key']] = json.loads(row['value'])
        except (json.JSONDecodeError, TypeError):
            config[row['key']] = row['value']
    return config


def set_schedule_config(key, value):
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        'INSERT OR REPLACE INTO ai_schedule_config (key, value, updated_at) VALUES (?, ?, ?)',
        (key, json.dumps(value) if not isinstance(value, str) else value, now)
    )
    conn.commit()
    conn.close()
