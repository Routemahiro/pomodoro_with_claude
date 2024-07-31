import logging
from core.timer import PomodoroTimer
import sqlite3
from datetime import datetime
import time

class EnhancedPomodoroTimer(PomodoroTimer):
    def __init__(self, work_time, short_break, long_break, on_tick, on_session_end, settings_manager, db_manager):
        super().__init__(work_time, short_break, long_break, on_tick, on_session_end, settings_manager)
        self.db_manager = db_manager
        self.current_session_id = None
        self.logger = logging.getLogger(__name__)

    def start(self):
        if not self.running:
            super().start()
            self.start_new_session()

    def _switch_session(self):
        self.logger.debug("Switching session")
        if self.current_session_id:
            self.end_current_session()  # 現在のセッションを終了
        self.is_work_session = not self.is_work_session
        self.session_count += 1
        if self.is_work_session:
            self.current_time = self.work_time
        else:
            self.current_time = self.short_break if self.session_count % 4 != 0 else self.long_break
        self.start_new_session()
        
        session_type = "work" if self.is_work_session else "break"
        if self.on_session_end is not None:
            previous_session_info = self.get_previous_session_info(session_type)
            self.on_session_end(self.is_work_session, previous_session_info)
        self.logger.debug(f"Switched to {'work' if self.is_work_session else 'break'} session")

    def start_new_session(self):
        if not self.current_session_id:
            self.current_session_id = self.db_manager.start_session("work" if self.is_work_session else "break")
            self.logger.debug(f"Started new session: {self.current_session_id}, type: {'work' if self.is_work_session else 'break'}")

    def end_current_session(self):
        if self.current_session_id:
            self.db_manager.end_session(self.current_session_id)  # セッションをデータベースで終了
            self.logger.debug(f"Ended session: {self.current_session_id}")
            self.current_session_id = None  # セッションIDをリセット
        else:
            self.logger.warning("Attempted to end session, but no current session ID")

    def get_previous_session_info(self, session_type):
        return self.db_manager.get_previous_session_info(session_type)

    def _run_timer(self):
        while self.running:
            if not self.paused:
                self.current_time -= 1
                self.on_tick(self.current_time, self.is_work_session)
                
                if self.current_time <= 0:
                    self._switch_session()
                    return  # タイマーが0になったら、ループを抜ける
                
            time.sleep(1)