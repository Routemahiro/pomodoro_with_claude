import sqlite3
import os
from datetime import datetime, timedelta
import threading

class DatabaseManager:
    def __init__(self, db_file='pomodoro.db'):
        self.db_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', db_file)
        self.conn = None
        self.lock = threading.Lock()
        self.create_tables()

    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        return self.conn

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # sessionsテーブルの作成 (ポモドーロサイクル全体を表す)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_number INTEGER NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME
                )
            ''')
            
            # pomodorosテーブルの作成 (個々のポモドーロを表す)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pomodoros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    pomodoro_type TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    completed BOOLEAN,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            ''')

            # app_usageテーブルの作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pomodoro_id INTEGER,
                    app_name TEXT NOT NULL,
                    window_name TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    FOREIGN KEY (pomodoro_id) REFERENCES pomodoros(id)
                )
            ''')
            
        print("データベーステーブルが正常に作成されました。")

    def start_session(self, cycle_number):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sessions (cycle_number, start_time)
                    VALUES (?, ?)
                ''', (cycle_number, datetime.now()))
                return cursor.lastrowid

    def end_session(self, session_id):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions
                    SET end_time = ?
                    WHERE id = ?
                ''', (datetime.now(), session_id))

    def start_pomodoro(self, session_id, pomodoro_type):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pomodoros (session_id, pomodoro_type, start_time)
                    VALUES (?, ?, ?)
                ''', (session_id, pomodoro_type, datetime.now()))
                return cursor.lastrowid

    def end_pomodoro(self, pomodoro_id, completed):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE pomodoros
                    SET end_time = ?, completed = ?
                    WHERE id = ?
                ''', (datetime.now(), completed, pomodoro_id))

    def record_activity(self, pomodoro_id, app_name, window_name, duration):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                duration = int(duration)
                cursor.execute('''
                    INSERT INTO app_usage (pomodoro_id, app_name, window_name, duration)
                    VALUES (?, ?, ?, ?)
                ''', (pomodoro_id, app_name, window_name, duration))

    def complete_pomodoro_cycle(self, session_id):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions
                    SET end_time = ?
                    WHERE id = ?
                ''', (datetime.now(), session_id))

    def get_daily_summary(self, date):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT app_name, SUM(duration) as total_duration
                    FROM app_usage
                    JOIN pomodoros ON app_usage.pomodoro_id = pomodoros.id
                    JOIN sessions ON pomodoros.session_id = sessions.id
                    WHERE DATE(sessions.start_time) = DATE(?)
                    GROUP BY app_name
                    ORDER BY total_duration DESC
                ''', (date,))
                return cursor.fetchall()

    def get_recent_activities(self, limit=10):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.app_name, a.window_name, p.pomodoro_type, p.start_time
                    FROM app_usage a
                    JOIN pomodoros p ON a.pomodoro_id = p.id
                    ORDER BY p.start_time DESC
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()

    def get_session_summary(self, session_id):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.start_time, s.end_time, s.cycle_number,
                           COUNT(DISTINCT p.id) as pomodoro_count,
                           GROUP_CONCAT(DISTINCT a.app_name) as used_apps
                    FROM sessions s
                    LEFT JOIN pomodoros p ON s.id = p.session_id
                    LEFT JOIN app_usage a ON p.id = a.pomodoro_id
                    WHERE s.id = ?
                    GROUP BY s.id
                ''', (session_id,))
                return cursor.fetchone()

    def get_previous_session_info(self, pomodoro_type):
        with self.lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, start_time, end_time
                    FROM pomodoros
                    WHERE pomodoro_type = ? AND end_time IS NOT NULL
                    ORDER BY end_time DESC
                    LIMIT 1
                ''', (pomodoro_type,))
                pomodoro = cursor.fetchone()

                if pomodoro:
                    pomodoro_id, start_time, end_time = pomodoro
                    start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M:%S")
                    end_time = datetime.fromisoformat(end_time).strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute('''
                        SELECT app_name, SUM(duration) as total_duration
                        FROM app_usage
                        WHERE pomodoro_id = ?
                        GROUP BY app_name
                        ORDER BY total_duration DESC
                        LIMIT 5
                    ''', (pomodoro_id,))
                    app_usage = cursor.fetchall()

                    info = f"前回の{pomodoro_type}セッション (開始: {start_time}, 終了: {end_time}):\n\n"
                    for app, duration in app_usage:
                        minutes, seconds = divmod(duration, 60)
                        info += f"{app}: {minutes}分{seconds:02d}秒\n"
                        cursor.execute('''
                            SELECT window_name, duration
                            FROM app_usage
                            WHERE pomodoro_id = ? AND app_name = ?
                            ORDER BY duration DESC
                            LIMIT 3
                        ''', (pomodoro_id, app))
                        top_windows = cursor.fetchall()
                        for window, window_duration in top_windows:
                            w_minutes, w_seconds = divmod(window_duration, 60)
                            info += f"  - {window}: {w_minutes}分{w_seconds:02d}秒\n"
                        info += "\n"
                    return info.strip()
                else:
                    return f"前回の{pomodoro_type}セッションのデータがありません。"

# デバッグ用の使用例
if __name__ == "__main__":
    db_manager = DatabaseManager()
    
    print("最近のアクティビティ:")
    for activity in db_manager.get_recent_activities(5):
        print(activity)
    
    print("\n最新セッションのサマリー:")
    latest_session = db_manager.start_session(1)
    summary = db_manager.get_session_summary(latest_session)
    print(summary)
    
    print("\n今日のアプリ使用状況:")
    for app_usage in db_manager.get_daily_summary(datetime.now().date()):
        print(app_usage)