import json
import os
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_FILE = "points_db.json"
PORT = int(os.environ.get("PORT", 8080))


def load_db():
    # Safely load database or return an empty dictionary if it doesn't exist yet
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
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        user = query.get("user", [""])
        touser = query.get("touser", [""])
        amount_str = query.get("amount", [""])

        # Clean strings cleanly
        user = user[0].strip().lower() if user else ""
        touser = touser[0].strip().lower() if touser else ""
        amount_str = amount_str[0].strip().lower() if amount_str else ""

        if not user:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Error: Missing user parameter.")
            return

        db = load_db()
        if user not in db:
            db[user] = 100  # Default starting balance

        response_msg = ""

        # --- !points command ---
        if path == "/points":
            target = touser if touser else user
            if target not in db:
                db[target] = 100
            response_msg = f"@{target.capitalize()} has {db[target]} points!"

        # --- !gamble command ---
        elif path == "/gamble":
            balance = db[user]
            if amount_str == "all":
                bet = balance
            else:
                try:
                    bet = int(amount_str)
                except ValueError:
                    bet = 0

            if bet <= 0:
                response_msg = (
                    f"@{user.capitalize()}, enter a valid amount to gamble!"
                )
            elif bet > balance:
                response_msg = f"@{user.capitalize()}, you only have {balance} points! You can't bet {bet}."
            else:
                roll = random.randint(1, 100)
                if roll > 50:  # 50% chance to win
                    db[user] += bet
                    response_msg = f"🎲 @{user.capitalize()} rolled a {roll} and WON {bet} points! New balance: {db[user]} 🎉"
                else:
                    db[user] -= bet
                    response_msg = f"📉 @{user.capitalize()} rolled a {roll} and LOST {bet} points. New balance: {db[user]} 💸"
        else:
            response_msg = "Invalid API endpoint."

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()
