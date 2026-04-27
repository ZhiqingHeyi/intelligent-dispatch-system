import threading
import time
from datetime import datetime
from ai_experience import get_all_ai_config, set_schedule_config, get_schedule_config
from ai_engine import ai_auto_dispatch


_scheduler_thread = None
_scheduler_running = False
_last_dispatch_time = None
_last_dispatch_result = None
_dispatch_count = 0


def start_ai_scheduler():
    global _scheduler_thread, _scheduler_running

    if _scheduler_running:
        return {'success': False, 'message': 'AI调度器已在运行中'}

    config = get_all_ai_config()
    if not config.get('api_key'):
        return {'success': False, 'message': '请先配置AI模型API Key'}

    _scheduler_running = True
    set_schedule_config('running', True)
    set_schedule_config('started_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def _loop():
        global _last_dispatch_time, _last_dispatch_result, _dispatch_count, _scheduler_running

        while _scheduler_running:
            try:
                config = get_all_ai_config()
                if not config.get('auto_dispatch_enabled') or not config.get('api_key'):
                    _scheduler_running = False
                    set_schedule_config('running', False)
                    break

                interval = config.get('dispatch_interval', 180)
                interval = max(30, min(interval, 3600))

                result = ai_auto_dispatch()
                _last_dispatch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                _last_dispatch_result = result
                _dispatch_count += 1
                set_schedule_config('last_dispatch_time', _last_dispatch_time)
                set_schedule_config('dispatch_count', _dispatch_count)

                print(f"[AI-SCHEDULER] 第{_dispatch_count}次自动调度完成: "
                      f"{'成功' if result.get('success') else '失败'}")

            except Exception as e:
                print(f"[AI-SCHEDULER] 自动调度异常: {e}")
                _last_dispatch_result = {'success': False, 'response': str(e)}

            wait_time = 0
            while _scheduler_running and wait_time < interval:
                time.sleep(1)
                wait_time += 1

        set_schedule_config('running', False)
        print("[AI-SCHEDULER] 调度器已停止")

    _scheduler_thread = threading.Thread(target=_loop, daemon=True)
    _scheduler_thread.start()

    return {'success': True, 'message': 'AI调度器已启动'}


def stop_ai_scheduler():
    global _scheduler_running
    _scheduler_running = False
    set_schedule_config('running', False)
    return {'success': True, 'message': 'AI调度器已停止'}


def get_scheduler_status():
    global _scheduler_running, _last_dispatch_time, _last_dispatch_result, _dispatch_count

    config = get_all_ai_config()
    schedule_config = get_schedule_config()

    return {
        'running': _scheduler_running,
        'enabled': config.get('auto_dispatch_enabled', False),
        'interval': config.get('dispatch_interval', 180),
        'api_configured': bool(config.get('api_key')),
        'last_dispatch_time': _last_dispatch_time or schedule_config.get('last_dispatch_time', ''),
        'last_dispatch_success': _last_dispatch_result.get('success') if _last_dispatch_result else None,
        'dispatch_count': _dispatch_count or schedule_config.get('dispatch_count', 0),
        'started_at': schedule_config.get('started_at', '')
    }
