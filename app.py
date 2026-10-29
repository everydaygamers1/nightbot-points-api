import json
import os
import random
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


class PointsAPIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urlparse(self.path)
        # Check both the path and query string parameters for total flexibility
        full_path_str = self.path.lower()
        query = parse_qs(parsed_url.query)

        # Extract values safely from queries
        user_param = query.get("user", [""])
        user = user_param[0].strip().lower() if user_param[0] else ""

        touser_param = query.get("touser", [""])
        touser = touser_param[0].strip().lower() if touser_param[0] else ""

        amount_param = query.get("amount", [""])
        amount_str = amount_param[0].strip().lower() if amount_param[0] else ""

        # Ultimate fallback parsing: if queries get mashed together by encoding bugs
        if not user:
            for key, val in query.items():
                if "user" in key.lower() and val:
                    user = val[0].strip().lower()
                if "touser" in key.lower() and val:
                    touser = val[0].strip().lower()
                if "amount" in key.lower() and val:
                    amount_str = val[0].strip().lower()

        # If it's hitting the bare homepage without parameters, tell them it's online
        if not user and "action" not in full_path_str:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Database API is online.")
            return

        db = load_db()
        if user and user not in db:
            db[user] = 100

        response_msg = ""

        # --- 🚀 TRIGGER CHECK: Looks for keywords anywhere in the link string ---
        if "points" in full_path_str or "action=points" in full_path_str:
            target = touser if touser else user
            if not target:
                response_msg = "Error: User parameter missing."
            else:
                if target not in db:
                    db[target] = 100
                response_msg = f"@{target.capitalize()} has {db[target]} points!"

        elif "gamble" in full_path_str or "action=gamble" in full_path_str:
            if not user:
                response_msg = "Error: User parameter missing."
            else:
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
                    if roll > 50:
                        db[user] += bet
                        response_msg = f"🎲 @{user.capitalize()} rolled a {roll} and WON {bet} points! New balance: {db[user]} 🎉"
                    else:
                        db[user] -= bet
                        response_msg = f"📉 @{user.capitalize()} rolled a {roll} and LOST {bet} points. New balance: {db[user]} 💸"
        else:
            response_msg = "Database API is online. Endpoints: points, gamble"

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()
