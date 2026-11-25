from datetime import date
from flask import Flask, jsonify, render_template, request
import sqlite3

app = Flask(__name__)

FOODS = [
    {"name": "سلطة خضار وفراخ مشوية", "calories": 420, "protein": 34, "carbs": 28, "fat": 18},
    {"name": "كبسة دجاج", "calories": 610, "protein": 38, "carbs": 72, "fat": 19},
    {"name": "باستا بالصلصة", "calories": 480, "protein": 16, "carbs": 76, "fat": 14},
    {"name": "فول وطعمية وسلطة", "calories": 390, "protein": 18, "carbs": 52, "fat": 12},
]


def get_db():
    connection = sqlite3.connect("wasfaty.db")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            protein INTEGER NOT NULL,
            carbs INTEGER NOT NULL,
            fat INTEGER NOT NULL,
            quantity REAL NOT NULL DEFAULT 1
        )
        """
    )
    return connection


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "يرجى اختيار صورة الوجبة"}), 400
    image = request.files["image"]
    if not image.filename:
        return jsonify({"error": "يرجى اختيار صورة الوجبة"}), 400

    # This demo classifier uses a sample prediction. A vision model can be
    # connected here without changing the frontend contract.
    return jsonify({"prediction": FOODS[0], "confidence": 94})


@app.route("/api/meals", methods=["GET", "POST", "DELETE"])
def meals():
    connection = get_db()
    if request.method == "POST":
        meal = request.get_json(silent=True) or {}
        required = ("name", "calories", "protein", "carbs", "fat")
        if not all(field in meal for field in required):
            connection.close()
            return jsonify({"error": "بيانات الوجبة غير مكتملة"}), 400

        cursor = connection.execute(
            """
            INSERT INTO meals (day, name, calories, protein, carbs, fat, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date.today().isoformat(),
                meal["name"],
                meal["calories"],
                meal["protein"],
                meal["carbs"],
                meal["fat"],
                meal.get("quantity", 1),
            ),
        )
        connection.commit()
        meal_id = cursor.lastrowid
        connection.close()
        return jsonify({"id": meal_id}), 201

    if request.method == "DELETE":
        meal_id = request.args.get("id", type=int)
        if not meal_id:
            connection.close()
            return jsonify({"error": "معرّف الوجبة مطلوب"}), 400
        connection.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        connection.commit()
        connection.close()
        return "", 204

    rows = connection.execute(
        "SELECT * FROM meals WHERE day = ? ORDER BY id DESC",
        (date.today().isoformat(),),
    ).fetchall()
    connection.close()
    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    app.run(debug=True)
