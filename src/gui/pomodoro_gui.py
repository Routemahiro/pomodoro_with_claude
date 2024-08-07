import tkinter as tk
from tkinter import ttk
from core.timer import PomodoroTimer
from gui.settings_gui import SettingsGUI
from core.enhanced_timer import EnhancedPomodoroTimer
from utils.database_manager import DatabaseManager
from utils.window_tracker import WindowTracker
from core.settings_manager import SettingsManager
import time
import threading
import datetime
from tkinter import font as tkfont
import logging

class PomodoroGUI:
    def __init__(self, master, settings_manager, window_tracker, db_manager):
        self.master = master
        self.settings_manager = settings_manager
        self.window_tracker = window_tracker
        self.db_manager = db_manager

        self.master.title("シュタインズ・ゲート風ポモドーロタイマー")
        self.master.geometry("600x400")
        self.master.configure(bg='#1e1e1e')

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', background='#4a4a4a', foreground='white')
        self.style.map('TButton', background=[('active', '#6a6a6a')])

        self.timer = EnhancedPomodoroTimer(
            self.settings_manager.get_setting('work_time'),
            self.settings_manager.get_setting('short_break'),
            self.settings_manager.get_setting('long_break'),
            self.update_timer_display,
            self.on_session_end,
            self.settings_manager,
            self.db_manager
        )

        self.last_update_time = time.time()
        self.smooth_progress = 0
        self.start_time = 0
        self.total_duration = 0

        self.current_session_id = None
        self.current_pomodoro_id = None
        self.tracking_thread = None

        self.create_widgets()

        logging.basicConfig(filename='pomodoro_gui_debug.log', level=logging.DEBUG)  # ロギングの設定
        self.logger = logging.getLogger(__name__)

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

        # セッション情報表示用のテキストウィジェットを追加
        self.session_info = tk.Text(self.master, height=10, width=50)
        self.session_info.pack(pady=10)

    def toggle_timer(self):
        self.logger.debug("Toggle timer called")
        if self.timer.running:
            if self.timer.paused:
                self.logger.debug("Resuming timer")
                self.timer.resume()
                self.start_pause_button.config(text="一時停止")
                self.start_time = time.time() - (self.total_duration - self.timer.current_time)
                self.db_manager.record_activity(self.timer.current_session_id, "Resume Pomodoro", "", 0)
                self.start_window_tracking()
            else:
                self.logger.debug("Pausing timer")
                self.timer.pause()
                self.start_pause_button.config(text="再開")
                self.db_manager.record_activity(self.timer.current_session_id, "Pause Pomodoro", "", 0)
                self.stop_window_tracking()
        else:
            self.logger.debug("Starting new timer")
            self.timer.start()
            self.start_pause_button.config(text="一時停止")
            self.start_time = time.time()
            self.total_duration = self.timer.current_time
            self.start_window_tracking()
            # 初回起動時に前回のセッション情報を表示
            self.show_previous_session_info("work" if self.timer.is_work_session else "break")
        self.update_button_states()
        self.smooth_update_progress()
        self.logger.debug(f"Timer state after toggle: running={self.timer.running}, paused={self.timer.paused}")

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
        self.logger.debug(f"Updated timer display: {minutes:02d}:{seconds:02d}, {'work' if is_work_session else 'break'} session")

    def smooth_update_progress(self):
        if self.timer.running and not self.timer.paused:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            progress = min(elapsed_time / self.total_duration, 1.0) * 100

            self.smooth_progress += (progress - self.smooth_progress) * 0.1
            self.progress_bar['value'] = self.smooth_progress

            self.master.after(16, self.smooth_update_progress)  # 約60FPSで更新
            
    def show_previous_session_info(self, session_type):
        self.logger.debug(f"Showing previous session info for {session_type}")  # セッション情報表示のログ
        info = self.db_manager.get_previous_session_info(session_type)
        self.session_info.delete(1.0, tk.END)
        
        if not info:
            self.logger.debug("No session info received")  # 情報が受信されなかったログ
            self.session_info.insert(tk.END, f"前回の{session_type}セッションのデータがありません。")
            return

        self.logger.debug(f"Received session info: {info}")  # 受信した情報のログ

        # フォントの設定
        default_font = tkfont.Font(font=self.session_info['font'])
        bold_font = tkfont.Font(font=self.session_info['font'])
        bold_font.configure(weight="bold")
        
        try:
            lines = info.split('\n')
            self.session_info.insert(tk.END, lines[0] + '\n\n', 'header')
            
            for line in lines[1:]:
                if ':' in line and not line.startswith('  -'):
                    # アプリケーション名の行
                    app_name, usage = line.split(':', 1)
                    self.session_info.insert(tk.END, app_name + ':', 'app_name')
                    self.session_info.insert(tk.END, usage + '\n')
                else:
                    # その他の行
                    self.session_info.insert(tk.END, line + '\n')
            
            # タグの設定
            self.session_info.tag_configure('header', font=bold_font, foreground='#4a4a4a')
            self.session_info.tag_configure('app_name', font=bold_font, foreground='#805AD5')
        except Exception as e:
            self.logger.error(f"Error displaying session info: {e}")  # エラーログ
            self.session_info.insert(tk.END, f"セッション情報の表示中にエラーが発生しました: {e}")

        # 表示されたテキストの長さを確認
        displayed_text = self.session_info.get("1.0", tk.END)
        self.logger.debug(f"Displayed text length: {len(displayed_text)}")  # 表示されたテキストの長さのログ
        self.logger.debug(f"Displayed text: {displayed_text}")  # 表示されたテキストのログ

    def on_session_end(self, is_work_session, previous_session_info):
        self.logger.debug(f"Session ended. New session: {'work' if is_work_session else 'break'}")
        self.stop_window_tracking()  # ウィンドウトラッキングを停止
        
        if not self.settings_manager.get_setting('auto_start'):
            self.start_pause_button.config(text="スタート")
        self.update_button_states()
        self.smooth_progress = 0
        self.progress_bar['value'] = 0
        self.start_time = time.time()
        self.total_duration = self.timer.current_time
        
        # 前回のセッション情報を表示
        self.show_previous_session_info("break" if is_work_session else "work")
        
        # 新しいセッションのウィンドウトラッキングを開始
        self.start_window_tracking()

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
                                                    args=(self.timer.current_session_id, self.current_pomodoro_id))
            self.tracking_thread.start()
        self.logger.debug(f"Started window tracking for session {self.timer.current_session_id}")

    def stop_window_tracking(self):
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.window_tracker.stop_tracking()  # ウィンドウトラッキングを停止
            self.tracking_thread.join(timeout=1)  # 最大1秒待機
            if self.tracking_thread.is_alive():
                self.logger.warning("Window tracking thread did not stop in time")
            self.tracking_thread = None
        self.logger.debug(f"Stopped window tracking for session {self.timer.current_session_id}")

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