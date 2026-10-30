import json
import os
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

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


def update_passive_points(db, username, is_live):
    """Guarantees a base of 100 points and updates passive watch time if live."""
    current_time = time.time()
    
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
        # 🚀 STEP 1: Scan the incoming string to see if the stream is live
        raw_path = self.path.lower()
        is_live = "live" in raw_path

        # 🚀 STEP 2: Pull the exact username straight out of Nightbot's native headers
        nb_user_header = self.headers.get("Nightbot-User", "")
        user = ""
        
        if nb_user_header:
            try:
                # Nightbot headers look like: name=chattername&displayName=ChatterName...
                for param in nb_user_header.split("&"):
                    if param.startswith("name="):
                        user = param.split("=")[1].strip().lower()
                        break
            except Exception:
                pass

        # Fallback if headers fail (like hitting it directly via browser)
        if not user:
            parsed_url = urlparse(self.path)
            query = parse_qs(parsed_url.query)
            user_param = query.get("user", [""])
            user = user_param[0].strip().lower() if user_param[0] else "guest"

        db = load_db()
        
        # Check if they are looking up someone else via standard query string
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        touser_param = query.get("touser", [""])
        touser = touser_param[0].strip().lower() if touser_param and touser_param[0] else ""

        # Silently process time blocks for the caller
        update_passive_points(db, user, is_live)
        
        # Calculate final points output
        target = touser if touser else user
        target_points = update_passive_points(db, target, is_live)
        
        save_db(db)

        # 🚀 STEP 3: Return ONLY the integer score string
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(str(target_points).encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()
