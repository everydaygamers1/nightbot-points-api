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
        # Decode and split the path parts cleanly by slashes
        raw_path = unquote(self.path).strip("/")
        parts = [p.lower().strip() for p in raw_path.split("/") if p.strip()]

        # Fallback if someone hits the main homepage domain directly
        if not parts:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Database API is online.")
            return

        command = parts[0]  # will be 'points' or 'gamble'
        db = load_db()
        response_msg = ""

        # --- 🚀 FLAT PATH 1: /points/username/target ---
        if "points" in command:
            user = parts[1] if len(parts) > 1 else ""
            touser = parts[2] if len(parts) > 2 else ""

            if not user:
                response_msg = "Error: Missing username."
            else:
                if user not in db:
                    db[user] = 100
                target = touser if touser else user
                if target not in db:
                    db[target] = 100
                response_msg = f"@{target.capitalize()} has {db[target]} points!"

        # --- 🚀 FLAT PATH 2: /gamble/username/betamount ---
        elif "gamble" in command:
            user = parts[1] if len(parts) > 1 else ""
            amount_str = parts[2] if len(parts) > 2 else ""

            if not user:
                response_msg = "Error: Missing username."
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
                    if roll > 50:
                        db[user] += bet
                        response_msg = f"🎲 @{user.capitalize()} rolled a {roll} and WON {bet} points! New balance: {db[user]} 🎉"
                    else:
                        db[user] -= bet
                        response_msg = f"📉 @{user.capitalize()} rolled a {roll} and LOST {bet} points. New balance: {db[user]} 💸"
        else:
            response_msg = "Invalid endpoint structure."

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()

