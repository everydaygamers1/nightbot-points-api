import json
import os
import random
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


class PointsAPIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # 🚀 SMART READING: Decode the incoming web string and break it down by words instead of folders
        raw_path = unquote(self.path).lower().replace("?", " ").replace("&", " ").replace("=", " ").replace("/", " ")
        words = [w.strip() for w in raw_path.split() if w.strip()]

        # Fallback response if the URL is completely bare
        if not words:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Database API is online. Core endpoints active.")
            return

        db = load_db()
        response_msg = ""

        # --- 🎮 SCENARIO A: CHATTER WANTS TO CHECK POINTS ---
        if "points" in words:
            # Safely locate usernames inside the word stream
            user = ""
            touser = ""
            
            if "user" in words:
                u_idx = words.index("user")
                if u_idx + 1 < len(words):
                    user = words[u_idx + 1]
            if "touser" in words:
                t_idx = words.index("touser")
                if t_idx + 1 < len(words):
                    touser = words[t_idx + 1]

            # Hard fallback if names didn't register cleanly
            if not user and len(words) > 1:
                user = words[1]

            if not user:
                response_msg = "Error parsing user profiles."
            else:
                if user not in db:
                    db[user] = 100  # Default starting balance
                target = touser if touser else user
                if target not in db:
                    db[target] = 100
                response_msg = f"@{target.capitalize()} has {db[target]} points!"

        # --- 🎲 SCENARIO B: CHATTER WANTS TO GAMBLE ---
        elif "gamble" in words:
            user = ""
            amount_str = ""

            if "user" in words:
                u_idx = words.index("user")
                if u_idx + 1 < len(words):
                    user = words[u_idx + 1]
            if "amount" in words:
                a_idx = words.index("amount")
                if a_idx + 1 < len(words):
                    amount_str = words[a_idx + 1]

            if not user and len(words) > 1:
                user = words[1]
            if not amount_str and len(words) > 2:
                amount_str = words[2]

            if not user:
                response_msg = "Error parsing user profile."
            elif not amount_str:
                response_msg = f"@{user.capitalize()}, enter a valid amount to gamble!"
            else:
                if user not in db:
                    db[user] = 100
                balance = db[user]

                if amount_str == "all":
                    bet = balance
                else:
                    try:
                        bet = int(amount_str)
                    except ValueError:
                        bet = 0

                if bet <= 0:
                    response_msg = f"@{user.capitalize()}, enter a valid amount to gamble!"
                elif bet > balance:
                    response_msg = f"@{user.capitalize()}, you only have {balance} points! You can't bet {bet}."
                else:
                    roll = random.randint(1, 100)
                    if roll > 50:  # 50% Win Rate
                        db[user] += bet
                        response_msg = f"🎲 @{user.capitalize()} rolled a {roll} and WON {bet} points! New balance: {db[user]} 🎉"
                    else:
                        db[user] -= bet
                        response_msg = f"📉 @{user.capitalize()} rolled a {roll} and LOST {bet} points. New balance: {db[user]} 💸"
        else:
            response_msg = "Database API is online."

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()
