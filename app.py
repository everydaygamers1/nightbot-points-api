import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote

DB_FILE = "points_db.json"
PORT = int(os.environ.get("PORT", 8080))


def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception as e:
        print(f"Error loading DB: {e}")
        return {}


def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving DB: {e}")


def update_passive_points(db, username, stream_status):
    """Guarantees a starting base of 100 points and updates passive time."""
    current_time = time.time()
    is_live = stream_status.lower() == "live"
    
    # 🚀 FIXED FORCE BASE: Absolutely forces 100 points if the profile doesn't exist
    if username not in db:
        db[username] = {
            "points": 100,
            "last_check": current_time
        }
        return 100
        
    if "points" not in db[username]:
        db[username]["points"] = 100

    if "last_check" not in db[username]:
        db[username]["last_check"] = current_time
        return db[username]["points"]

    elapsed_seconds = current_time - db[username]["last_check"]
    five_min_blocks = int(elapsed_seconds // 300)
    
    if five_min_blocks > 0:
        if is_live:
            db[username]["points"] += (five_min_blocks * 100)
            db[username]["last_check"] += (five_min_blocks * 300)
        else:
            db[username]["last_check"] = current_time
        
    return db[username]["points"]


class PointsAPIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Decode request string and split cleanly by space characters
        raw_path = unquote(self.path).lower().replace("?", " ").replace("&", " ").replace("=", " ").replace("/", " ")
        words = [w.strip() for w in raw_path.split() if w.strip()]

        # 🚀 FALLBACK FOR BARE HOMEPAGE
        if not words or "points" not in words:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"100")
            return

        db = load_db()
        
        user = ""
        touser = ""
        status = "offline" 
        
        if "user" in words:
            u_idx = words.index("user")
            if u_idx + 1 < len(words):
                user = words[u_idx + 1]
        if "touser" in words:
            t_idx = words.index("touser")
            if t_idx + 1 < len(words):
                touser = words[t_idx + 1]
        if "status" in words:
            s_idx = words.index("status")
            if s_idx + 1 < len(words):
                status = words[s_idx + 1]

        # Ultimate fallback if text array fails to locate flags
        if not user and len(words) > 1:
            user = words[1]

        if not user:
            response_msg = "100"
        else:
            update_passive_points(db, user, status)
            target = touser if touser else user
            target_points = update_passive_points(db, target, status)
            response_msg = str(target_points)

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()

