import ctypes
import ctypes.wintypes
import time

class WindowTracker:
    def __init__(self, db_manager):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.psapi = ctypes.windll.psapi
        self.db_manager = db_manager
        self.running = True

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

    def start_tracking(self, session_id, pomodoro_id):
        last_window_info = None
        start_time = time.time()

        while self.running:
            window_info = self.get_active_window_info()
            
            if window_info != last_window_info:
                if last_window_info:
                    duration = int(time.time() - start_time)
                    self.db_manager.record_activity(session_id, last_window_info['app_name'], last_window_info['window_name'], duration)
                
                last_window_info = window_info
                start_time = time.time()
            
            time.sleep(1)  # 1秒ごとにチェック

    def stop_tracking(self):
        self.running = False

# 使用例
if __name__ == "__main__":
    from database_manager import DatabaseManager
    db_manager = DatabaseManager()
    tracker = WindowTracker(db_manager)
    
    def print_window_info(info):
        print(f"アプリ名: {info['app_name']}, ウィンドウ名: {info['window_name']}")

    tracker.start_tracking(1, 1)  # セッションIDとポモドーロIDを仮に1とする