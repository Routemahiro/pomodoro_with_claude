import tkinter as tk
from tkinter import ttk
from core.timer import PomodoroTimer
from gui.settings_gui import SettingsGUI
from utils.database_manager import DatabaseManager
from utils.window_tracker import WindowTracker
from core.settings_manager import SettingsManager  # この行を追加
import time
import threading

class PomodoroGUI:
    def __init__(self, master, settings_manager, window_tracker, db_manager):
        self.master = master
        self.settings_manager = settings_manager
        self.window_tracker = window_tracker
        self.db_manager = db_manager

        self.master.title("シュタインズ・ゲート風ポモドーロタイマー")
        self.master.geometry("400x350")
        self.master.configure(bg='#1e1e1e')

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', background='#4a4a4a', foreground='white')
        self.style.map('TButton', background=[('active', '#6a6a6a')])

        self.timer = PomodoroTimer(
            self.settings_manager.get_setting('work_time'),
            self.settings_manager.get_setting('short_break'),
            self.settings_manager.get_setting('long_break'),
            self.update_timer_display,
            self.on_session_end,
            self.settings_manager
        )

        self.last_update_time = time.time()
        self.smooth_progress = 0
        self.start_time = 0
        self.total_duration = 0

        self.current_session_id = None
        self.current_pomodoro_id = None
        self.tracking_thread = None

        self.create_widgets()

    def create_widgets(self):
        initial_time = self.settings_manager.get_setting('work_time')
        self.timer_display = tk.Label(self.master, text=f"{initial_time:02d}:00", font=("Courier", 48), fg='#00ff00', bg='#1e1e1e')
        self.timer_display.pack(pady=20)

        self.session_label = tk.Label(self.master, text="作業セッション", font=("Helvetica", 14), fg='white', bg='#1e1e1e')
        self.session_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=300, mode="determinate", style="Quantum.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=10)

        self.style.configure("Quantum.Horizontal.TProgressbar", 
                             troughcolor='#1e1e1e', 
                             background='#805AD5',
                             lightcolor='#B794F4',
                             darkcolor='#6B46C1')

        button_frame = tk.Frame(self.master, bg='#1e1e1e')
        button_frame.pack(pady=20)

        self.start_pause_button = ttk.Button(button_frame, text="エル・プサイ・コングルゥ", command=self.toggle_timer)
        self.start_pause_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(button_frame, text="リセット", command=self.reset_timer)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.settings_button = ttk.Button(button_frame, text="設定", command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=5)

    def toggle_timer(self):
        if self.timer.running:
            if self.timer.paused:
                self.timer.resume()
                self.start_pause_button.config(text="一時停止")
                self.start_time = time.time() - (self.total_duration - self.timer.current_time)
                self.db_manager.record_activity(self.current_session_id, self.current_pomodoro_id, "Resume Pomodoro", "")
                self.start_window_tracking()
            else:
                self.timer.pause()
                self.start_pause_button.config(text="再開")
                self.db_manager.record_activity(self.current_session_id, self.current_pomodoro_id, "Pause Pomodoro", "")
                self.stop_window_tracking()
        else:
            self.timer.start()
            self.start_pause_button.config(text="一時停止")
            self.start_time = time.time()
            self.total_duration = self.timer.current_time
            self.current_session_id = self.db_manager.start_session("work" if self.timer.is_work_session else "break")
            self.current_pomodoro_id = self.db_manager.start_pomodoro()
            self.start_window_tracking()
        self.update_button_states()
        self.smooth_update_progress()

    def reset_timer(self):
        if self.current_session_id:
            self.db_manager.end_session(self.current_session_id)
        if self.current_pomodoro_id:
            self.db_manager.end_pomodoro(self.current_pomodoro_id, False)
        self.stop_window_tracking()
        self.timer.reset()
        initial_time = self.settings_manager.get_setting('work_time')
        self.update_timer_display(initial_time * 60, True)
        self.start_pause_button.config(text="エル・プサイ・コングルゥ")
        self.update_button_states()
        self.smooth_progress = 0
        self.progress_bar['value'] = 0
        self.start_time = 0
        self.total_duration = initial_time * 60
        self.current_session_id = None
        self.current_pomodoro_id = None

    def update_timer_display(self, time_left, is_work_session):
        minutes, seconds = divmod(time_left, 60)
        self.timer_display.config(text=f"{minutes:02d}:{seconds:02d}")
        self.session_label.config(text="作業セッション" if is_work_session else "休憩セッション")

    def smooth_update_progress(self):
        if self.timer.running and not self.timer.paused:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            progress = min(elapsed_time / self.total_duration, 1.0) * 100

            self.smooth_progress += (progress - self.smooth_progress) * 0.1
            self.progress_bar['value'] = self.smooth_progress

            self.master.after(16, self.smooth_update_progress)  # 約60FPSで更新

    def on_session_end(self, is_work_session):
        if self.current_session_id:
            self.db_manager.end_session(self.current_session_id)
        if self.current_pomodoro_id:
            self.db_manager.end_pomodoro(self.current_pomodoro_id, True)
        
        if not self.settings_manager.get_setting('auto_start'):
            self.start_pause_button.config(text="スタート")
        self.update_button_states()
        self.smooth_progress = 0
        self.progress_bar['value'] = 0
        self.start_time = time.time()
        self.total_duration = self.timer.work_time if is_work_session else (self.timer.short_break if self.timer.session_count % 4 != 0 else self.timer.long_break)
        
        # 新しいセッションとポモドーロの開始をデータベースに記録
        self.current_session_id = self.db_manager.start_session("work" if is_work_session else "break")
        self.current_pomodoro_id = self.db_manager.start_pomodoro()
        self.stop_window_tracking()

    def open_settings(self):
        if not self.timer.running:
            SettingsGUI(self.master, self.settings_manager, self.apply_settings)

    def apply_settings(self):
        self.timer.update_settings(
            self.settings_manager.get_setting('work_time'),
            self.settings_manager.get_setting('short_break'),
            self.settings_manager.get_setting('long_break')
        )
        self.reset_timer()

    def update_button_states(self):
        if self.timer.running:
            self.settings_button.state(['disabled'])
            self.reset_button.state(['!disabled'])
        else:
            self.settings_button.state(['!disabled'])
            self.reset_button.state(['disabled'])

    def start_window_tracking(self):
        if self.tracking_thread is None or not self.tracking_thread.is_alive():
            self.tracking_thread = threading.Thread(target=self.window_tracker.start_tracking, 
                                                    args=(self.current_session_id, self.current_pomodoro_id))
            self.tracking_thread.start()

    def stop_window_tracking(self):
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=1)  # 最大1秒待機
            if self.tracking_thread.is_alive():
                # ここでスレッドを強制終了する方法を実装する必要があります
                pass

    def run(self):
        self.update_button_states()
        self.master.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    settings_manager = SettingsManager()
    db_manager = DatabaseManager()
    window_tracker = WindowTracker(db_manager)
    app = PomodoroGUI(root, settings_manager, window_tracker, db_manager)
    app.run()