import tkinter as tk
from tkinter import ttk

class SettingsGUI:
    def __init__(self, master, settings_manager, apply_callback):
        self.settings_manager = settings_manager
        self.apply_callback = apply_callback

        self.window = tk.Toplevel(master)
        self.window.title("設定")
        self.window.geometry("300x250")
        self.window.configure(bg='#1e1e1e')

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', background='#1e1e1e', foreground='white')
        self.style.configure('TEntry', fieldbackground='#4a4a4a', foreground='white')

        self.create_widgets()

    def create_widgets(self):
        settings_frame = ttk.Frame(self.window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(settings_frame, text="作業時間 (分):").grid(row=0, column=0, sticky="w", pady=5)
        self.work_time_entry = ttk.Entry(settings_frame)
        self.work_time_entry.grid(row=0, column=1, pady=5)
        self.work_time_entry.insert(0, self.settings_manager.get_setting('work_time'))

        ttk.Label(settings_frame, text="短い休憩 (分):").grid(row=1, column=0, sticky="w", pady=5)
        self.short_break_entry = ttk.Entry(settings_frame)
        self.short_break_entry.grid(row=1, column=1, pady=5)
        self.short_break_entry.insert(0, self.settings_manager.get_setting('short_break'))

        ttk.Label(settings_frame, text="長い休憩 (分):").grid(row=2, column=0, sticky="w", pady=5)
        self.long_break_entry = ttk.Entry(settings_frame)
        self.long_break_entry.grid(row=2, column=1, pady=5)
        self.long_break_entry.insert(0, self.settings_manager.get_setting('long_break'))

        ttk.Label(settings_frame, text="自動開始:").grid(row=3, column=0, sticky="w", pady=5)
        self.auto_start_var = tk.BooleanVar(value=self.settings_manager.get_setting('auto_start'))
        self.auto_start_check = ttk.Checkbutton(settings_frame, variable=self.auto_start_var)
        self.auto_start_check.grid(row=3, column=1, pady=5)

        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="適用", command=self.apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def apply_settings(self):
        try:
            work_time = int(self.work_time_entry.get())
            short_break = int(self.short_break_entry.get())
            long_break = int(self.long_break_entry.get())

            if work_time <= 0 or short_break <= 0 or long_break <= 0:
                raise ValueError("時間は正の整数である必要があります。")

            self.settings_manager.update_setting('work_time', work_time)
            self.settings_manager.update_setting('short_break', short_break)
            self.settings_manager.update_setting('long_break', long_break)
            self.settings_manager.update_setting('auto_start', self.auto_start_var.get())

            self.apply_callback()
            self.window.destroy()
        except ValueError as e:
            tk.messagebox.showerror("エラー", str(e))