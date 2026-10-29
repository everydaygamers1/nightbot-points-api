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
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # 🚀 UNIVERSAL PARSING: Grabs the username from parameters or secure headers safely
        user = ""
        nb_user_header = self.headers.get("Nightbot-User", "")

        if nb_user_header and "name=" in nb_user_header:
            try:
                # Extracts username out of complex string safely
                parts = nb_user_header.split("name=")
                if len(parts) > 1:
                    user = parts[1].split("&")[0].strip().lower()
            except Exception:
                pass

        if not user:
            # Fallback to standard parameter if headers aren't parsed
            user_param = query.get("user", [""])
            user = user_param[0].strip().lower() if user_param[0] else ""

        # Handle optional variables safely
        touser_param = query.get("touser", [""])
        touser = touser_param[0].strip().lower() if touser_param[0] else ""

        amount_param = query.get("amount", [""])
        amount_str = amount_param[0].strip().lower() if amount_param[0] else ""

        if not user:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Error: Missing username configuration.")
            return

        db = load_db()
        if user not in db:
            db[user] = 100

        response_msg = ""

        # 🚀 FLEXIBLE PATHS: Matches whether the path has a trailing slash, queries, or headers
        if "points" in path:
            target = touser if touser else user
            if target not in db:
                db[target] = 100
            response_msg = f"@{target.capitalize()} has {db[target]} points!"

        elif "gamble" in path:
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
            response_msg = "Database API is online. Endpoints: /points, /gamble"

        save_db(db)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(response_msg.encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), PointsAPIHandler)
    print(f"Server alive on port {PORT}...")
    server.serve_forever()
