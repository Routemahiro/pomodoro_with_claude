import logging
from core.timer import PomodoroTimer
import sqlite3
from datetime import datetime

class EnhancedPomodoroTimer(PomodoroTimer):
    def __init__(self, work_time, short_break, long_break, on_tick, on_session_end, settings_manager, db_manager):
        super().__init__(work_time, short_break, long_break, on_tick, on_session_end, settings_manager)
        self.db_manager = db_manager
        self.current_session_id = None
        self.logger = logging.getLogger(__name__)

    def start(self):
        super().start()
        self.start_new_session()

    def _switch_session(self):
        if self.current_session_id:
            self.end_current_session()
        super()._switch_session()
        self.start_new_session()
        
        # セッション切り替え時に前回のセッション情報を取得
        session_type = "break" if self.is_work_session else "work"  # 切り替わった後なので、前のセッションタイプを指定
        
        # on_session_end コールバックを通じて情報を渡す
        if self.on_session_end is not None:
            previous_session_info = self.get_previous_session_info(session_type)  # 前回のセッション情報を取得
            self.on_session_end(self.is_work_session, previous_session_info)  # 修正

    def start_new_session(self):
        self.current_session_id = self.db_manager.start_session("work" if self.is_work_session else "break")
        self.logger.debug(f"Started new session: {self.current_session_id}, type: {'work' if self.is_work_session else 'break'}")

    def end_current_session(self):
        if self.current_session_id:
            self.db_manager.end_session(self.current_session_id)
            self.logger.debug(f"Ended session: {self.current_session_id}")
        else:
            self.logger.warning("Attempted to end session, but no current session ID")

    def record_app_usage(self, app_name, window_name, duration):
        if self.current_session_id:
            self.db_manager.record_activity(self.current_session_id, app_name, window_name, duration)
            self.logger.debug(f"Recorded app usage: {app_name}, {window_name}, {duration}")
        else:
            self.logger.warning("Attempted to record app usage, but no current session ID")

    def get_previous_session_info(self, session_type):
        return self.db_manager.get_previous_session_info(session_type)