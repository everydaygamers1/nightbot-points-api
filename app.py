import json
import os
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_FILE = "points_db.json"
# Render automatically injects a dynamic configuration PORT environment variable
PORT = int(os.environ.get("PORT", 8080))


def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


class PointsAPIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        user = query.get("user", [""]).strip().lower()
        touser = query.get("touser", [""]).strip().lower()
        amount_str = query.get("amount", [""]).strip()

        if not user:
            self.send_response(400)
            self.end_headers()
            return

        db = load_db()
        if user not in db:
            db[user] = 100  # Starting points for new chatters

        response_msg = ""

        # --- !points command logic ---
        if path == "/points":
            target = touser if touser else user
            if target not in db:
                db[target] = 100
            response_msg = f"@{target.capitalize()} has {db[target]} points!"

        # --- !gamble command logic ---
        elif path == "/gamble":
            balance = db[user]
            if amount_str.lower() == "all":
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
                if roll > 50:  # 50% Win Rate
                    db[user] += bet
                    response_msg = f"🎲 @{user.capitalize()} rolled a {roll} and WON {bet} points! New balance: {db[user]} 🎉"
                else:
                    db[user] -= bet
                    response_msg = f"📉 @{user.capitalize()} rolled a {roll} and LOST {bet} points. New balance: {db[user]} 💸"

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    # Binding the web service interface container to handle incoming cloud network requests
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()
