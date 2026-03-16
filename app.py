from pyexpat.errors import messages

from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "secret123"


def get_db():
    return sqlite3.connect("database.db")


def create_anon_id():
    code = ''.join(random.choices(string.hexdigits, k=4))
    return "Anon_" + code


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        anon_id TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()


init_db()
@app.route("/", methods=["GET","POST"])
def index():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        message = request.form["message"]

        c.execute(
            "INSERT INTO messages(user_id,text) VALUES (?,?)",
            (session["user_id"], message)
        )

        conn.commit()

    c.execute("""
    SELECT messages.id, messages.text, users.anon_id, messages.likes, messages.dislikes
    FROM messages
    JOIN users ON messages.user_id = users.id
    ORDER BY messages.id DESC
    """)

    messages = c.fetchall()

    c.execute("SELECT username, anon_id FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()

    conn.close()

    return render_template("index.html", messages=messages, user=user)

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        anon_id = create_anon_id()

        conn = get_db()
        c = conn.cursor()

        c.execute(
            "INSERT INTO users(username,password,anon_id) VALUES (?,?,?)",
            (username,password,anon_id)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/like/<int:msg_id>")
def like(msg_id):

    conn = get_db()
    c = conn.cursor()

    c.execute("UPDATE messages SET likes = likes + 1 WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/dislike/<int:msg_id>")
def dislike(msg_id):

    conn = get_db()
    c = conn.cursor()

    c.execute("UPDATE messages SET dislikes = dislikes + 1 WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()

    return redirect("/")
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        c.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = c.fetchone()

        if user:
            session["user_id"] = user[0]
            return redirect("/")

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)