"""
プレイ記録(タップのタイミング等)をCSVと「SQL(テキストのINSERT文)」の
両方に保存するモジュール。

保存する項目:
    played_at     : 記録した日時 (YYYY-MM-DD HH:MM:SS)
    session_id    : 同じプレイ回(1回のリトライ〜終了まで)をまとめる番号
    difficulty    : そのプレイの難易度 ("EASY" / "NORMAL" / "HARD")
    sentence_id   : どの英文(ステージ)か
    target_word   : どの単語を押した/押すべきだったか
    word_index    : 文中の何番目の単語か (0始まり)
    target_time   : 正解時刻(秒)
    tap_time      : 実際に押した時刻(秒)。押さずにMISSした場合はNone
    timing_error  : tap_time - target_time (秒)。tap_timeがNoneの場合はNone
    result        : "PERFECT" / "GOOD" / "MISS"

play_log.csv … 表計算ソフトで開ける形式
play_log.sql … そのままSQLiteやMySQL等に流し込める、CREATE TABLE + INSERT文のテキスト

パフォーマンスについて:
    以前はログを1件書くたびにファイル/DB接続を開いて閉じていたため、
    プレイ中に毎回わずかな処理落ちが発生していました。
    このバージョンではファイルを開いたまま保持し、追記だけを行うようにしています。
"""

import csv
import os
import time

CSV_HEADERS = [
    "played_at",
    "session_id",
    "difficulty",
    "sentence_id",
    "target_word",
    "word_index",
    "target_time",
    "tap_time",
    "timing_error",
    "result",
]

CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS play_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    played_at TEXT NOT NULL,
    session_id TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    target_word TEXT NOT NULL,
    word_index INTEGER NOT NULL,
    target_time REAL NOT NULL,
    tap_time REAL,
    timing_error REAL,
    result TEXT NOT NULL
);"""


def _sql_literal(value) -> str:
    """PythonのオブジェクトをSQLのリテラル表記に変換する。"""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return str(value)


class PlayLogger:
    def __init__(self, base_dir: str, csv_name: str = "play_log.csv", sql_name: str = "play_log.sql"):
        self.csv_path = os.path.join(base_dir, csv_name)
        self.sql_path = os.path.join(base_dir, sql_name)

        self._init_csv()
        self._init_sql()

        # ファイルは開いたままにしておき、ログを書くたびに開き直さないようにする
        # (毎回開閉すると、タップのたびに処理落ちの原因になるため)
        self._csv_file = open(self.csv_path, "a", newline="", encoding="utf-8-sig")
        self._csv_writer = csv.writer(self._csv_file)
        self._sql_file = open(self.sql_path, "a", encoding="utf-8")

    def _backup_path(self, path: str) -> str:
        base, ext = os.path.splitext(path)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"{base}_old_{timestamp}{ext}"

    def _init_csv(self) -> None:
        if os.path.isfile(self.csv_path):
            try:
                with open(self.csv_path, "r", newline="", encoding="utf-8-sig") as f:
                    first_line = f.readline().strip()
                if first_line != ",".join(CSV_HEADERS):
                    backup_path = self._backup_path(self.csv_path)
                    os.rename(self.csv_path, backup_path)
                    print(f"[log] 列構成が変わったため、古いCSVを {backup_path} に退避しました")
            except OSError:
                pass

        if not os.path.isfile(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(CSV_HEADERS)

    def _init_sql(self) -> None:
        if os.path.isfile(self.sql_path):
            try:
                with open(self.sql_path, "r", encoding="utf-8") as f:
                    head = f.read(1000)
                if "difficulty" not in head:
                    backup_path = self._backup_path(self.sql_path)
                    os.rename(self.sql_path, backup_path)
                    print(f"[log] 列構成が変わったため、古いSQLを {backup_path} に退避しました")
            except OSError:
                pass

        if not os.path.isfile(self.sql_path):
            with open(self.sql_path, "w", encoding="utf-8") as f:
                f.write(CREATE_TABLE_SQL + "\n\n")

    def log(
        self,
        session_id: str,
        difficulty: str,
        sentence_id: str,
        target_word: str,
        word_index: int,
        target_time: float,
        tap_time,
        result: str,
    ) -> None:
        played_at = time.strftime("%Y-%m-%d %H:%M:%S")
        timing_error = None if tap_time is None else round(tap_time - target_time, 4)

        row = (
            played_at,
            session_id,
            difficulty,
            sentence_id,
            target_word,
            word_index,
            round(target_time, 4),
            None if tap_time is None else round(tap_time, 4),
            timing_error,
            result,
        )

        try:
            self._csv_writer.writerow(row)
            self._csv_file.flush()
        except OSError as e:
            print(f"[log] CSVへの書き込みに失敗しました: {e}")

        try:
            columns = ", ".join(CSV_HEADERS)
            values = ", ".join(_sql_literal(v) for v in row)
            self._sql_file.write(f"INSERT INTO play_log ({columns}) VALUES ({values});\n")
            self._sql_file.flush()
        except OSError as e:
            print(f"[log] SQLファイルへの書き込みに失敗しました: {e}")

    def close(self) -> None:
        try:
            self._csv_file.close()
        except OSError:
            pass
        try:
            self._sql_file.close()
        except OSError:
            pass
