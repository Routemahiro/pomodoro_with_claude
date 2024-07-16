import sqlite3
import os
from datetime import datetime, timedelta
import threading

class DatabaseManager:
    def __init__(self, db_file='pomodoro.db'):
        self.db_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', db_file)
        self.local = threading.local()
        self.create_tables()

    def get_connection(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_file)
        return self.local.conn

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # テーブル作成のSQLステートメント（変更なし）

    def start_session(self, session_type):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (start_time, session_type)
                VALUES (?, ?)
            ''', (datetime.now(), session_type))
            return cursor.lastrowid

    def end_session(self, session_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sessions
                SET end_time = ?
                WHERE session_id = ?
            ''', (datetime.now(), session_id))

    def start_pomodoro(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pomodoros (start_time)
                VALUES (?)
            ''', (datetime.now(),))
            return cursor.lastrowid

    def end_pomodoro(self, pomodoro_id, completed):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pomodoros
                SET end_time = ?, completed = ?
                WHERE pomodoro_id = ?
            ''', (datetime.now(), completed, pomodoro_id))

    def record_activity(self, session_id, pomodoro_id, app_name, window_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activities (session_id, pomodoro_id, timestamp, app_name, window_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, pomodoro_id, datetime.now(), app_name, window_name))

    def get_daily_summary(self, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT app_name, SUM(duration) as total_duration
                FROM activities
                WHERE DATE(timestamp) = DATE(?)
                GROUP BY app_name
                ORDER BY total_duration DESC
            ''', (date,))
            return cursor.fetchall()

    def get_recent_activities(self, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.timestamp, a.app_name, a.window_name, s.session_type
                FROM activities a
                JOIN sessions s ON a.session_id = s.session_id
                ORDER BY a.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()

    def get_session_summary(self, session_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.start_time, s.end_time, s.session_type,
                       COUNT(a.activity_id) as activity_count,
                       GROUP_CONCAT(DISTINCT a.app_name) as used_apps
                FROM sessions s
                LEFT JOIN activities a ON s.session_id = a.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id
            ''', (session_id,))
            return cursor.fetchone()

    def get_daily_app_usage(self, date=None):
        if date is None:
            date = datetime.now().date()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT app_name, COUNT(*) as use_count
                FROM activities
                WHERE DATE(timestamp) = DATE(?)
                GROUP BY app_name
                ORDER BY use_count DESC
            ''', (date,))
            return cursor.fetchall()

# デバッグ用の使用例
if __name__ == "__main__":
    db_manager = DatabaseManager()
    
    print("最近のアクティビティ:")
    for activity in db_manager.get_recent_activities(5):
        print(activity)
    
    print("\n最新セッションのサマリー:")
    latest_session = db_manager.start_session("work")
    summary = db_manager.get_session_summary(latest_session)
    print(summary)
    
    print("\n今日のアプリ使用状況:")
    for app_usage in db_manager.get_daily_app_usage():
        print(app_usage)
