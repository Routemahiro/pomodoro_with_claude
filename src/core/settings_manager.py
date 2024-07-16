import json
import os

class SettingsManager:
    def __init__(self, config_file='config.json'):
        self.config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', config_file)
        self.default_settings = {
            'work_time': 25,
            'short_break': 5,
            'long_break': 15,
            'auto_start': True
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.config_file) or os.path.getsize(self.config_file) == 0:
            print("設定ファイルが存在しないか空です。デフォルト設定を使用し、ファイルを作成します。")
            self.save_settings(self.default_settings)
            return self.default_settings.copy()

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("設定ファイルの解析に失敗しました。デフォルト設定を使用し、ファイルを上書きします。")
            self.save_settings(self.default_settings)
            return self.default_settings.copy()

    def save_settings(self, settings=None):
        if settings is None:
            settings = self.settings
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(settings, f, indent=4)

    def get_setting(self, key):
        return self.settings.get(key, self.default_settings.get(key))

    def update_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def reset_to_default(self):
        self.settings = self.default_settings.copy()
        self.save_settings()