import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from matplotlib import font_manager
from datetime import datetime, timedelta

class AppUsageVisualization:
    def __init__(self, master):
        self.master = master
        self.master.title("アプリケーション使用状況")
        self.master.geometry("800x400")  # ウィンドウサイズを大きくしました

        self.frame = tk.Frame(self.master)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 日本語フォントの設定
        font_path = 'C:/Windows/Fonts/meiryo.ttc'
        font_prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()

        self.create_widgets()

    def create_widgets(self):
        # 左側のフレーム（グラフ用）
        left_frame = tk.Frame(self.frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右側のフレーム（ランキングとコントロール用）
        right_frame = tk.Frame(self.frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 日付範囲選択
        date_range_frame = tk.Frame(right_frame)
        date_range_frame.pack(pady=5)
        tk.Label(date_range_frame, text="開始日:").pack(side=tk.LEFT)
        self.start_date = DateEntry(date_range_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date.pack(side=tk.LEFT, padx=5)
        tk.Label(date_range_frame, text="終了日:").pack(side=tk.LEFT)
        self.end_date = DateEntry(date_range_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        # デフォルトで今日の日付を設定
        today = datetime.now().date()
        self.start_date.set_date(today)
        self.end_date.set_date(today)

        # 更新ボタン
        update_button = ttk.Button(right_frame, text="更新", command=self.update_visualization)
        update_button.pack(pady=5)

        # ランキングのラベル
        self.ranking_label = tk.Label(right_frame, text="使用時間", font=("Meiryo", 12))
        self.ranking_label.pack(pady=5)

        # スクロール可能なテキストウィジェット
        self.text_widget = tk.Text(right_frame, wrap=tk.WORD, width=30, height=15)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # スクロールバーの追加
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        # グラフ用のキャンバス
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.update_visualization()

    def update_visualization(self):
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()

        # データの取得（ここでは仮のデータを生成）
        app_usage = self.generate_sample_data(start_date, end_date)

        self.create_pie_chart(app_usage, start_date, end_date)
        self.create_ranking(app_usage)

    def create_pie_chart(self, app_usage, start_date, end_date):
        self.ax.clear()
        top_5 = dict(sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:5])
        other = sum(app_usage.values()) - sum(top_5.values())
        if other > 0:
            top_5['その他'] = other

        colors = plt.cm.Set3(range(len(top_5)))
        wedges, texts, autotexts = self.ax.pie(top_5.values(), labels=top_5.keys(), autopct='%1.1f%%', 
                                               startangle=90, colors=colors)
        self.ax.axis('equal')
        self.ax.set_title(f"トップ5アプリケーション使用状況\n({start_date} ~ {end_date})", fontsize=10)

        plt.setp(texts, size=8)
        plt.setp(autotexts, size=8)

        self.canvas.draw()

    def create_ranking(self, app_usage):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)

        sorted_usage = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)
        for i, (app, usage) in enumerate(sorted_usage, 1):
            self.text_widget.insert(tk.END, f"{i}. {app}: {usage:.2f}時間\n")
            self.text_widget.tag_add(app, f"{i}.3", f"{i}.{3+len(app)}")
            self.text_widget.tag_bind(app, "<Button-1>", lambda e, a=app: self.show_app_details(a))

        self.text_widget.config(state=tk.DISABLED)

    def generate_sample_data(self, start_date, end_date):
        apps = ['VS Code', 'Chrome', 'Notepad', 'PowerPoint', 'Skype', 'Firefox', 'Word', 'Zoom', 
                'Outlook', 'Illustrator', 'Photoshop', 'Slack', 'Excel', 'Teams', 'Terminal']
        
        days = (end_date - start_date).days + 1
        return {app: random.uniform(0.5 * days, 8 * days) for app in apps}

    def show_app_details(self, app_name):
        details_window = tk.Toplevel(self.master)
        details_window.title(f"{app_name} の使用履歴")
        details_window.geometry("600x400")

        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        tk.Label(details_window, text=f"{app_name} の詳細な使用履歴 ({start_date} ~ {end_date})", font=("Meiryo", 14)).pack(pady=10)

        tree = ttk.Treeview(details_window, columns=('日付', '時間', 'ウィンドウ'), show='headings')
        tree.heading('日付', text='日付')
        tree.heading('時間', text='使用時間')
        tree.heading('ウィンドウ', text='ウィンドウ名')
        tree.column('日付', width=100, anchor='center')
        tree.column('時間', width=100, anchor='center')
        tree.column('ウィンドウ', width=350, anchor='w')
        tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)

        current_date = start_date
        while current_date <= end_date:
            usage = random.uniform(0.1, 2)
            window_name = self.generate_sample_window_name(app_name)
            tree.insert('', 'end', values=(current_date.strftime('%Y-%m-%d'), f"{usage:.2f}時間", window_name))
            current_date += timedelta(days=1)

    def generate_sample_window_name(self, app_name):
        if app_name == 'Chrome':
            websites = ['Google - Chrome', 'YouTube - Chrome', 'GitHub - Chrome', 'Stack Overflow - Chrome']
            return random.choice(websites)
        elif app_name == 'VS Code':
            files = ['main.py - Visual Studio Code', 'index.html - Visual Studio Code', 'styles.css - Visual Studio Code']
            return random.choice(files)
        elif app_name == 'Word':
            documents = ['レポート.docx - Word', '議事録.docx - Word', 'プレゼン資料.docx - Word']
            return random.choice(documents)
        else:
            return f"{app_name} - ランダムなドキュメント"

if __name__ == "__main__":
    root = tk.Tk()
    app = AppUsageVisualization(root)
    root.mainloop()