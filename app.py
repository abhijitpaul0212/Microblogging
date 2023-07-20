import datetime
import os
from flask import Flask, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    client = MongoClient(os.getenv("MONGODB_URI"))
    # Create a new Database
    app.db = client.microblog

    @app.route("/", methods=["GET", "POST"])
    def home():
        if request.method == "POST":
            entry_content = request.form.get("content")
            formatted_date = datetime.datetime.today().strftime("%Y-%m-%d")
            app.db.entries.insert_one({"content": entry_content, "date": formatted_date})
        
        entries_with_date = [(entry.get("content"), entry.get("date"), datetime.datetime.strptime(entry.get("date"), "%Y-%m-%d").strftime("%b %d")) for entry in app.db.entries.find({})]

        return render_template("home.html", entries=entries_with_date)
    return app

# if __name__ == "__main__":
#     app.run(debug=True)
