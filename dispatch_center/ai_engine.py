import json
import requests
from database import get_db
from ai_config import SYSTEM_PROMPT, TOOLS, AI_DEFAULT_CONFIG
from ai_experience import (
    save_chat_message, get_chat_history,
    save_experience, get_experience, get_experience_summary,
    save_dispatch_log, get_all_ai_config
)
from database import create_dispatch_task, complete_dispatch_task, cancel_dispatch_task

GRADE_NAMES = {
    1: '二级配',
    2: '三级配',
    3: '四级配',
    4: '三级配PVA纤维',
    5: '三级富浆',
}


def _get_config():
    return get_all_ai_config()


def _build_context_message():
    db = get_db()
    cable_cars = [dict(r) for r in db.execute('SELECT * FROM cable_cars ORDER BY id').fetchall()]
    vehicles = [dict(r) for r in db.execute('SELECT * FROM vehicles ORDER BY tid').fetchall()]
    active_tasks = [dict(r) for r in db.execute(
        '''SELECT t.*, cc.name as cable_car_name, v.name as vehicle_name, gc.name as grade_name
           FROM dispatch_tasks t
           LEFT JOIN cable_cars cc ON t.cable_car_id = cc.id
           LEFT JOIN vehicles v ON t.vehicle_id = v.id
           LEFT JOIN grade_config gc ON t.grade_id = gc.id
           WHERE t.status IN ('assigned', 'pending')'''
    ).fetchall()]
    db.close()

    context = "【当前系统实时状态】\n\n"
    context += "=== 缆机状态 ===\n"
    for car in cable_cars:
        grade_name = GRADE_NAMES.get(car.get('grade_id', 0), '未设置')
        context += (f"  {car['name']}(ID={car['id']}): "
                    f"状态={car.get('state_label', car.get('state', '未知'))}, "
                    f"级配={grade_name}, "
                    f"位置latitude={car.get('latitude', 0):.1f}, "
                    f"xspeed={car.get('xspeed', 0):.2f}, "
                    f"调度状态={car.get('status', 'idle')}\n")

    context += "\n=== 车辆状态 ===\n"
    for v in vehicles:
        grade_name = GRADE_NAMES.get(v.get('grade_id', 0), '未设置')
        # 使用新的状态标签
        state_label = v.get('state_label', '')
        if not state_label:
            # 向后兼容：如果state_label为空，基于state或direction推断
            state = v.get('state', '')
            direction = v.get('direction', '')
            state_map = {
                'standby': '待命',
                'delivering': '送料中',
                'delivering_pause': '送料暂停',
                'unloading': '卸料中',
                'unloading_wait': '卸料等待',
                'returning': '返程中'
            }
            state_label = state_map.get(state, '') or {'going': '送料中', 'returning': '返程中', 'stopped': '待命', 'idle': '待命'}.get(direction, '待命')

        # 显示Y坐标区域信息
        result_y = v.get('result_y', 0)
        if result_y > 50:
            zone = "接料区"
        elif result_y < -950:
            zone = "卸料区"
        else:
            zone = "送料途中"

        context += (f"  {v['name']}(ID={v['id']}): "
                    f"状态={state_label}({zone}), "
                    f"级配={grade_name}, "
                    f"Y坐标={result_y:.1f}, "
                    f"速度={v.get('speed', 0):.1f}, "
                    f"调度状态={v.get('status', 'idle')}\n")

    context += "\n=== 当前任务 ===\n"
    if active_tasks:
        for t in active_tasks:
            context += (f"  任务#{t['id']}: {t.get('cable_car_name', '?')} ↔ {t.get('vehicle_name', '?')} "
                        f"({t.get('grade_name', '?')}) 状态={t['status']}\n")
    else:
        context += "  暂无进行中任务\n"

    summary = get_experience_summary()
    context += f"\n=== AI调度经验统计 ===\n"
    context += f"  总调度次数: {summary['total']}, 成功: {summary['success']}, "
    context += f"失败: {summary['failure']}, 待确认: {summary['pending']}, "
    context += f"成功率: {summary['success_rate']}%, 被调度员修正: {summary['overrides']}次\n"

    return context


def _execute_tool(name, arguments):
    try:
        if name == 'query_current_status':
            return _tool_query_current_status()
        elif name == 'create_dispatch_task':
            return _tool_create_dispatch_task(arguments)
        elif name == 'complete_dispatch_task':
            return _tool_complete_dispatch_task(arguments)
        elif name == 'cancel_dispatch_task':
            return _tool_cancel_dispatch_task(arguments)
        elif name == 'get_dispatch_experience':
            return _tool_get_experience(arguments)
        elif name == 'get_position_ranking':
            return _tool_get_position_ranking()
        else:
            return json.dumps({'error': f'未知工具: {name}'}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'error': str(e)}, ensure_ascii=False)


def _tool_query_current_status():
    db = get_db()
    cable_cars = [dict(r) for r in db.execute('SELECT * FROM cable_cars ORDER BY id').fetchall()]
    vehicles = [dict(r) for r in db.execute('SELECT * FROM vehicles ORDER BY tid').fetchall()]
    active_tasks = [dict(r) for r in db.execute(
        '''SELECT t.*, cc.name as cable_car_name, v.name as vehicle_name, gc.name as grade_name
           FROM dispatch_tasks t
           LEFT JOIN cable_cars cc ON t.cable_car_id = cc.id
           LEFT JOIN vehicles v ON t.vehicle_id = v.id
           LEFT JOIN grade_config gc ON t.grade_id = gc.id
           WHERE t.status IN ('assigned', 'pending')'''
    ).fetchall()]
    db.close()

    for car in cable_cars:
        car['grade_name'] = GRADE_NAMES.get(car.get('grade_id', 0), '未设置')
    for v in vehicles:
        v['grade_name'] = GRADE_NAMES.get(v.get('grade_id', 0), '未设置')

    return json.dumps({
        'cable_cars': cable_cars,
        'vehicles': vehicles,
        'active_tasks': active_tasks
    }, ensure_ascii=False, default=str)


def _tool_create_dispatch_task(args):
    cable_car_id = args.get('cable_car_id')
    vehicle_id = args.get('vehicle_id')
    grade_id = args.get('grade_id')
    reason = args.get('reason', '')

    db = get_db()
    car = db.execute('SELECT * FROM cable_cars WHERE id = ?', (cable_car_id,)).fetchone()
    vehicle = db.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,)).fetchone()

    if not car or not vehicle:
        db.close()
        return json.dumps({'success': False, 'message': '缆机或车辆不存在'}, ensure_ascii=False)

    if car['grade_id'] != grade_id or vehicle['grade_id'] != grade_id:
        db.close()
        return json.dumps({
            'success': False,
            'message': f'级配不匹配: 缆机级配={GRADE_NAMES.get(car["grade_id"], "未设置")}, 车辆级配={GRADE_NAMES.get(vehicle["grade_id"], "未设置")}, 要求级配={GRADE_NAMES.get(grade_id, "未知")}'
        }, ensure_ascii=False)

    existing_car = db.execute(
        'SELECT id FROM dispatch_tasks WHERE cable_car_id = ? AND status IN ("assigned","pending")',
        (cable_car_id,)
    ).fetchone()
    if existing_car:
        db.close()
        return json.dumps({'success': False, 'message': f'{car["name"]}已有进行中的任务'}, ensure_ascii=False)

    existing_v = db.execute(
        'SELECT id FROM dispatch_tasks WHERE vehicle_id = ? AND status IN ("assigned","pending")',
        (vehicle_id,)
    ).fetchone()
    if existing_v:
        db.close()
        return json.dumps({'success': False, 'message': f'{vehicle["name"]}已有进行中的任务'}, ensure_ascii=False)

    db.close()

    task_id = create_dispatch_task(cable_car_id, vehicle_id, grade_id)

    save_dispatch_log(task_id, cable_car_id, vehicle_id, grade_id, 'create', reason, 'ai')
    save_experience(
        cable_car_id, vehicle_id, grade_id, reason,
        cable_car_state=car.get('state', ''),
        vehicle_state=vehicle.get('direction', ''),
        cable_car_latitude=car.get('latitude', 0),
        vehicle_result_y=vehicle.get('result_y', 0)
    )

    return json.dumps({
        'success': True,
        'task_id': task_id,
        'message': f'调度成功: {car["name"]} ↔ {vehicle["name"]} ({GRADE_NAMES.get(grade_id, "未知级配")})'
    }, ensure_ascii=False)


def _tool_complete_dispatch_task(args):
    task_id = args.get('task_id')
    try:
        complete_dispatch_task(task_id)
        save_dispatch_log(task_id, 0, 0, 0, 'complete', args.get('reason', ''), 'ai')
        return json.dumps({'success': True, 'message': f'任务#{task_id}已完成'}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'success': False, 'message': str(e)}, ensure_ascii=False)


def _tool_cancel_dispatch_task(args):
    task_id = args.get('task_id')
    reason = args.get('reason', '')
    try:
        cancel_dispatch_task(task_id)
        save_dispatch_log(task_id, 0, 0, 0, 'cancel', reason, 'ai')
        return json.dumps({'success': True, 'message': f'任务#{task_id}已取消'}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'success': False, 'message': str(e)}, ensure_ascii=False)


def _tool_get_experience(args):
    grade_id = args.get('grade_id')
    outcome = args.get('outcome', 'all')
    limit = args.get('limit', 10)
    experiences = get_experience(grade_id=grade_id, outcome=outcome, limit=limit)
    return json.dumps(experiences, ensure_ascii=False, default=str)


def _tool_get_position_ranking():
    db = get_db()
    returning_cars = [dict(r) for r in db.execute(
        '''SELECT * FROM cable_cars
           WHERE (state IN ('returning', 'loading') OR direction = 'returning')
           AND status NOT IN ('assigned')
           ORDER BY latitude ASC'''
    ).fetchall()]
    going_vehicles = [dict(r) for r in db.execute(
        '''SELECT * FROM vehicles
           WHERE direction = 'going' AND status = 'going' AND grade_id > 0
           AND id NOT IN (SELECT vehicle_id FROM dispatch_tasks WHERE status = 'assigned')
           ORDER BY result_y ASC'''
    ).fetchall()]
    db.close()

    result = {
        'returning_cable_cars_by_position': [],
        'going_vehicles_by_position': []
    }

    for i, car in enumerate(returning_cars):
        grade_name = GRADE_NAMES.get(car.get('grade_id', 0), '未设置')
        result['returning_cable_cars_by_position'].append({
            'rank': i + 1,
            'id': car['id'],
            'name': car['name'],
            'state': car.get('state', ''),
            'grade': grade_name,
            'grade_id': car.get('grade_id', 0),
            'latitude': car.get('latitude', 0),
            'note': 'latitude越小越靠近装料区，优先级越高'
        })

    for i, v in enumerate(going_vehicles):
        grade_name = GRADE_NAMES.get(v.get('grade_id', 0), '未设置')
        result['going_vehicles_by_position'].append({
            'rank': i + 1,
            'id': v['id'],
            'name': v['name'],
            'grade': grade_name,
            'grade_id': v.get('grade_id', 0),
            'result_y': v.get('result_y', 0),
            'speed': v.get('speed', 0),
            'note': 'result_y越小越靠近卸料区，优先匹配'
        })

    return json.dumps(result, ensure_ascii=False, default=str)


def chat_with_ai(user_message, auto_dispatch=False):
    config = _get_config()

    if not config.get('api_key'):
        return {
            'response': '⚠️ AI模型未配置，请先在设置中配置API Key。',
            'tool_results': [],
            'success': False
        }

    context_msg = _build_context_message()

    history = get_chat_history(limit=20)
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT + '\n\n' + context_msg}]

    for msg in history[-16:]:
        if msg['role'] in ('user', 'assistant'):
            messages.append({'role': msg['role'], 'content': msg['content']})

    if auto_dispatch:
        messages.append({
            'role': 'user',
            'content': '请分析当前系统状态，执行智能调度匹配。按照位置优先级和级配匹配规则，为所有等待中的缆机匹配最合适的车辆。如果当前没有可匹配的对象，说明原因。'
        })
    else:
        messages.append({'role': 'user', 'content': user_message})

    save_chat_message('user', user_message if not auto_dispatch else '[自动调度] 执行智能调度匹配')

    tool_results = []
    final_response = ''
    max_iterations = 5

    for iteration in range(max_iterations):
        try:
            api_response = requests.post(
                config['api_url'],
                headers={
                    'Authorization': f'Bearer {config["api_key"]}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config.get('model', 'gpt-4o'),
                    'messages': messages,
                    'tools': TOOLS,
                    'tool_choice': 'auto',
                    'temperature': config.get('temperature', 0.3),
                    'max_tokens': config.get('max_tokens', 2048)
                },
                timeout=60
            )
            api_response.raise_for_status()
            result = api_response.json()
        except requests.exceptions.Timeout:
            final_response = '⚠️ AI模型响应超时，请稍后重试。'
            save_chat_message('assistant', final_response)
            return {'response': final_response, 'tool_results': tool_results, 'success': False}
        except requests.exceptions.ConnectionError:
            final_response = '⚠️ 无法连接到AI模型服务，请检查API地址和网络连接。'
            save_chat_message('assistant', final_response)
            return {'response': final_response, 'tool_results': tool_results, 'success': False}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            if status_code == 401:
                final_response = '⚠️ API Key无效，请检查配置。'
            elif status_code == 429:
                final_response = '⚠️ API调用频率超限，请稍后重试。'
            elif status_code == 404:
                final_response = '⚠️ 模型不存在，请检查模型名称配置。'
            else:
                final_response = f'⚠️ AI模型服务错误({status_code})，请检查配置。'
            save_chat_message('assistant', final_response)
            return {'response': final_response, 'tool_results': tool_results, 'success': False}
        except Exception as e:
            final_response = f'⚠️ 调用AI模型失败: {str(e)}'
            save_chat_message('assistant', final_response)
            return {'response': final_response, 'tool_results': tool_results, 'success': False}

        choice = result['choices'][0]
        assistant_msg = choice['message']
        messages.append(assistant_msg)

        if assistant_msg.get('content'):
            final_response = assistant_msg['content']

        if assistant_msg.get('tool_calls'):
            for tool_call in assistant_msg['tool_calls']:
                func_name = tool_call['function']['name']
                try:
                    func_args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    func_args = {}

                tool_output = _execute_tool(func_name, func_args)

                tool_result_data = {
                    'tool_name': func_name,
                    'arguments': func_args,
                    'result': json.loads(tool_output) if isinstance(tool_output, str) else tool_output
                }
                tool_results.append(tool_result_data)

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call['id'],
                    'content': tool_output
                })

                save_chat_message('assistant',
                                  f'[调用工具: {func_name}]',
                                  tool_calls=[{'name': func_name, 'arguments': func_args}],
                                  tool_result=tool_result_data)

            if choice.get('finish_reason') == 'tool_calls':
                continue
        else:
            break

    if final_response:
        save_chat_message('assistant', final_response)
    else:
        final_response = 'AI已完成分析，但未生成文本回复。请查看工具调用结果。'
        save_chat_message('assistant', final_response)

    return {
        'response': final_response,
        'tool_results': tool_results,
        'success': True
    }


def ai_auto_dispatch():
    return chat_with_ai('', auto_dispatch=True)
