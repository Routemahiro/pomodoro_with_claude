import time
import threading

class PomodoroTimer:
    def __init__(self, work_time, short_break, long_break, on_tick, on_session_end, settings_manager):
        self.work_time = work_time * 60
        self.short_break = short_break * 60
        self.long_break = long_break * 60
        self.on_tick = on_tick
        self.on_session_end = on_session_end
        self.settings_manager = settings_manager
        
        self.current_time = self.work_time
        self.is_work_session = True
        self.session_count = 0
        self.running = False
        self.paused = False
        
        self.timer_thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.timer_thread = threading.Thread(target=self._run_timer)
            self.timer_thread.start()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def reset(self):
        self.running = False
        if self.timer_thread:
            self.timer_thread.join()
        self.current_time = self.work_time
        self.is_work_session = True
        self.session_count = 0
        self.paused = False

    def _run_timer(self):
        while self.running:
            if not self.paused:
                self.current_time -= 1
                self.on_tick(self.current_time, self.is_work_session)
                
                if self.current_time <= 0:
                    self._switch_session()
                
                time.sleep(1)

    def _switch_session(self):
        self.session_count += 1
        if self.is_work_session:
            if self.session_count % 4 == 0:
                self.current_time = self.long_break
            else:
                self.current_time = self.short_break
            self.is_work_session = False
        else:
            self.current_time = self.work_time
            self.is_work_session = True
        
        self.on_session_end(self.is_work_session)
        
        if not self.settings_manager.get_setting('auto_start'):
            self.pause()

    def update_settings(self, work_time, short_break, long_break):
        self.work_time = work_time * 60
        self.short_break = short_break * 60
        self.long_break = long_break * 60
        if not self.running:
            self.current_time = self.work_time