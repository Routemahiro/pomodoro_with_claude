from core.timer import PomodoroTimer
from datetime import datetime, timedelta

class EnhancedPomodoroTimer(PomodoroTimer):
    def __init__(self, work_time, short_break, long_break, on_tick, on_session_end, settings_manager, db_manager):
        super().__init__(work_time, short_break, long_break, on_tick, on_session_end, settings_manager)
        self.db_manager = db_manager
        self.current_session_id = None
        self.current_pomodoro_id = None
        self.cycle_count = 0
        self.pomodoros_in_cycle = 0

    def start(self):
        super().start()
        self.start_new_cycle()

    def _switch_session(self):
        if self.current_pomodoro_id:
            self.end_current_pomodoro()
        
        self.pomodoros_in_cycle += 1
        if self.pomodoros_in_cycle > 7:  # 4 work + 3 short breaks + 1 long break
            self.complete_pomodoro_cycle()
            self.start_new_cycle()
        else:
            super()._switch_session()
            self.start_new_pomodoro()

        session_type = "work" if self.is_work_session else "break"
        if self.on_session_end is not None:
            previous_session_info = self.get_previous_session_info(session_type)
            self.on_session_end(self.is_work_session, previous_session_info)

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