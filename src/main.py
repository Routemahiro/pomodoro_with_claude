import tkinter as tk
from gui.pomodoro_gui import PomodoroGUI
from core.settings_manager import SettingsManager
from utils.window_tracker import WindowTracker
from utils.database_manager import DatabaseManager

def main():
    root = tk.Tk()
    settings_manager = SettingsManager()
    db_manager = DatabaseManager()
    window_tracker = WindowTracker(db_manager)
    
    app = PomodoroGUI(root, settings_manager, window_tracker, db_manager)
    
    root.mainloop()

if __name__ == "__main__":
    main()

    # 課題：連続で切り替えが呼び出されてるっぽいのが見えたから、これを修正する必要がある。