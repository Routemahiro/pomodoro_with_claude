import ctypes
import ctypes.wintypes

class WindowTracker:
    def __init__(self, db_manager):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.psapi = ctypes.windll.psapi
        self.db_manager = db_manager

    def get_active_window_info(self):
        hwnd = self.user32.GetForegroundWindow()
        
        # ウィンドウ名を取得
        window_name = ctypes.create_unicode_buffer(255)
        self.user32.GetWindowTextW(hwnd, window_name, 255)
        
        # プロセスIDを取得
        pid = ctypes.wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # プロセス名（アプリ名）を取得
        hProcess = self.kernel32.OpenProcess(0x1000, False, pid)
        try:
            exe_path = (ctypes.c_char * 260)()
            self.psapi.GetModuleFileNameExA(hProcess, None, exe_path, 260)
            exe_name = exe_path.value.decode('utf-8').split('\\')[-1]
            app_name = exe_name.split('.')[0]  # 拡張子を除去
        finally:
            self.kernel32.CloseHandle(hProcess)
        
        return {
            'app_name': app_name,
            'window_name': window_name.value
        }

    def track_active_window(self, callback, interval=30):
        import time
        while True:
            window_info = self.get_active_window_info()
            callback(window_info)
            time.sleep(interval)

    def start_tracking(self, session_id, pomodoro_id, interval=30):
        import time
        while True:
            window_info = self.get_active_window_info()
            self.db_manager.record_activity(session_id, pomodoro_id, window_info['app_name'], window_info['window_name'])
            time.sleep(interval)

# 使用例
if __name__ == "__main__":
    from database_manager import DatabaseManager
    db_manager = DatabaseManager()
    tracker = WindowTracker(db_manager)
    
    def print_window_info(info):
        print(f"アプリ名: {info['app_name']}, ウィンドウ名: {info['window_name']}")

    tracker.track_active_window(print_window_info, interval=5)  # 5秒ごとに取得