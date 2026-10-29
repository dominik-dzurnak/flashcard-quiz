from flask import Flask, render_template, request, redirect
import sqlite3
import random
import csv

app = Flask(__name__)

DATABASE = "quiz.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            topic TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            known INTEGER NOT NULL
        )
    """)

    # if the database is empty, load sample questions from questions.csv
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    if count == 0:
        with open("questions.csv", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                conn.execute("INSERT INTO questions (question, answer, topic) VALUES (?, ?, ?)",
                             (row["question"], row["answer"], row["topic"]))

    conn.commit()
    conn.close()


@app.route("/")
def quiz():
    conn = get_connection()
    questions = conn.execute("SELECT * FROM questions").fetchall()
    conn.close()

    if len(questions) == 0:
        return render_template("quiz.html", question=None)

    question = random.choice(questions)
    return render_template("quiz.html", question=question)


@app.route("/answer", methods=["POST"])
def save_answer():
    question_id = request.form["question_id"]
    known = request.form["known"]  # 1 = I knew it, 0 = I didn't know

    conn = get_connection()
    conn.execute("INSERT INTO results (question_id, known) VALUES (?, ?)", (question_id, known))
    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/add", methods=["GET", "POST"])
def add_question():
    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"]
        topic = request.form["topic"]

        conn = get_connection()
        conn.execute("INSERT INTO questions (question, answer, topic) VALUES (?, ?, ?)",
                     (question, answer, topic))
        conn.commit()
        conn.close()

        return redirect("/add")

    return render_template("add.html")


@app.route("/score")
def score():
    conn = get_connection()
    rows = conn.execute("""
        SELECT questions.topic, SUM(results.known) AS known, COUNT(results.id) AS total
        FROM results
        JOIN questions ON results.question_id = questions.id
        GROUP BY questions.topic
    """).fetchall()
    conn.close()

    return render_template("score.html", rows=rows)


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
