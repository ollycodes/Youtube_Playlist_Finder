from dataclasses import dataclass
import sqlite3, os, json

DB_NAME = "cache.db"

@dataclass
class CacheTools:
    conn: sqlite3.Connection
    cur: sqlite3.Cursor

    def __init__(self):
        if not os.path.exists(DB_NAME):
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS API (
                    id INTEGER PRIMARY KEY,
                    call TEXT UNIQUE,
                    response TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS VIDEOS (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    video_id TEXT UNIQUE,
                    duration INTEGER,
                    chapters TEXT
                )
                """
            )
            conn.commit()
        self.conn = sqlite3.connect(DB_NAME)
        self.cur = self.conn.cursor()

    def save_api_call(self, api: dict):
        call, response = api["call"], api["response"]
        self.cur.execute(
            """
            INSERT INTO API (call, response)
            VALUES (?, ?)
            """, (call, response)
        )
        self.commit_and_close()

    def save_video(self, video):
        self.cur.execute(
            """
            SELECT * FROM VIDEOS WHERE video_id = ?
            """, (video.video_id,)
        )
        chapters_string = json.dumps(video.chapters)
        if self.cur.fetchone():
            self.cur.execute(
                """
                UPDATE VIDEOS SET title = ?, duration = ?, chapters = ?
                WHERE video_id = ?
                """, (video.title, video.duration, chapters_string, video.video_id)
            )
        else:
            self.cur.execute(
                """
                INSERT INTO VIDEOS (title, video_id, duration, chapters)
                VALUES (?, ?, ?, ?)
                """, (video.title, video.video_id, video.duration, chapters_string)
            )
        self.commit_and_close()

    def load_video(self, video_id):
        self.cur.execute(
            """
            SELECT title, video_id, duration, chapters FROM VIDEOS
            WHERE video_id = ?
            """, (video_id,)
        )
        data = self.cur.fetchone()
        data["chapters"] = json.loads(data["chapters"])
        self.commit_and_close()
        return data

    def check_api_cache(self, cache_key:str):
        self.cur.execute(
            """
            SELECT response FROM API
            WHERE call = ?
            """, (cache_key,)
        )
        cache = self.cur.fetchone()
        return json.loads(*cache) if cache is not None else None

    def commit_and_close(self) -> None:
        self.conn.commit()
        self.cur.close()
        self.conn.close()

def use_api_cache(api_func):
    def wrapper(*args, **kwargs):
        cache_key = str(api_func.__name__) + str(args) + str(kwargs)
        response = CacheTools().check_api_cache(cache_key)
        if response is None:
            response = api_func(*args, **kwargs)
            CacheTools().save_api_call({"call": cache_key, "response": json.dumps(response)})
        return response
    wrapper.uncached = api_func
    return wrapper
