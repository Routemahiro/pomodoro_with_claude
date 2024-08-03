from core.timer import PomodoroTimer
from datetime import datetime, timedelta
import time

class EnhancedPomodoroTimer(PomodoroTimer):
    def __init__(self, work_time, short_break, long_break, on_tick, on_session_end, settings_manager, db_manager):
        super().__init__(work_time, short_break, long_break, on_tick, on_session_end, settings_manager)
        self.db_manager = db_manager
        self.current_session_id = None
        self.current_pomodoro_id = None
        self.cycle_count = 0
        self.pomodoros_in_cycle = 0
        self.last_switch_time = None
        self.min_session_duration = timedelta(seconds=30)  # 最小セッション時間を30秒に設定

    def start(self):
        super().start()
        self.start_new_cycle()

    def _run_timer(self):
        while self.running:
            if not self.paused:
                current_time = datetime.now()
                if self.current_time <= 0 and (self.last_switch_time is None or (current_time - self.last_switch_time) >= self.min_session_duration):
                    self._switch_session()
                else:
                    self.current_time -= 1
                    self.on_tick(self.current_time, self.is_work_session)
                
                time.sleep(1)

    def _switch_session(self):
        current_time = datetime.now()
        if self.last_switch_time and (current_time - self.last_switch_time) < self.min_session_duration:
            print(f"セッション切り替えが早すぎます。無視します。")
            self.current_time = 1  # 次のティックで再度チェック
            return

        if self.current_pomodoro_id:
            self.end_current_pomodoro()
        
        self.pomodoros_in_cycle += 1
        if self.pomodoros_in_cycle > 7:  # 4 work + 3 short breaks + 1 long break
            self.complete_pomodoro_cycle()
            self.start_new_cycle()
        else:
            if self.is_work_session:
                if self.pomodoros_in_cycle % 4 == 0:
                    self.current_time = self.long_break
                else:
                    self.current_time = self.short_break
                self.is_work_session = False
            else:
                self.current_time = self.work_time
                self.is_work_session = True
            
            self.start_new_pomodoro()

        session_type = "work" if self.is_work_session else "break"
        if self.on_session_end is not None:
            previous_session_info = self.get_previous_session_info(session_type)
            self.on_session_end(self.is_work_session, previous_session_info)

        self.last_switch_time = current_time

        if not self.settings_manager.get_setting('auto_start'):
            self.pause()

    def start_new_cycle(self):
        self.cycle_count += 1
        self.pomodoros_in_cycle = 0
        self.current_session_id = self.db_manager.start_session(f"cycle_{self.cycle_count}")
        self.start_new_pomodoro()

    def complete_pomodoro_cycle(self):
        if self.current_session_id:
            self.db_manager.end_session(self.current_session_id)
        self.db_manager.complete_pomodoro_cycle(self.current_session_id)

    def start_new_pomodoro(self):
        pomodoro_type = "work" if self.is_work_session else ("long_break" if self.pomodoros_in_cycle == 7 else "short_break")
        self.current_pomodoro_id = self.db_manager.start_pomodoro(self.current_session_id, pomodoro_type)

    def end_current_pomodoro(self):
        if self.current_pomodoro_id:
            self.db_manager.end_pomodoro(self.current_pomodoro_id, True)

    def record_app_usage(self, app_name, window_name, duration):
        if self.current_pomodoro_id:
            self.db_manager.record_activity(self.current_pomodoro_id, app_name, window_name, duration)

    def get_previous_session_info(self, session_type):
        return self.db_manager.get_previous_session_info(session_type)

    def reset(self):
        super().reset()
        if self.current_session_id:
            self.db_manager.end_session(self.current_session_id)
        if self.current_pomodoro_id:
            self.db_manager.end_pomodoro(self.current_pomodoro_id, False)
        self.cycle_count = 0
        self.pomodoros_in_cycle = 0
        self.current_session_id = None
        self.current_pomodoro_id = None
        self.last_switch_time = None