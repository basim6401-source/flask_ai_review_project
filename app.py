from flask import Flask, render_template, jsonify, request, redirect, url_for
import random
import os
import json

app = Flask(__name__)

GOOGLE_REVIEW_URL = "https://search.google.com/local/writereview?placeid=ChIJEb5DJgBDvDsRixDy-RGkGCw"

food_items = [
    "burger",
    "fries",
    "fried chicken",
    "milkshake",
    "wrap",
    "combo meal",
    "chicken sandwich",
    "loaded fries",
    "taco",
    "salad"
]

qualities = [
    "perfectly cooked",
    "fresh and flavorful",
    "crispy and juicy",
    "really satisfying",
    "hot and tasty",
    "rich in flavor",
    "well-seasoned",
    "super fresh",
    "deliciously prepared",
    "excellent quality"
]

service_phrases = [
    "The staff were friendly and efficient, and the whole experience felt smooth.",
    "Service was quick, the team was welcoming, and the food arrived exactly as expected.",
    "Everything came out fast and the customer service was genuinely great.",
    "The place was clean, the staff were polite, and the order was handled perfectly.",
    "The service was outstanding and made the visit even more enjoyable."
]

review_starters = [
    "I really loved the",
    "The",
    "This place does a great job with the",
    "The food here was",
    "I was pleasantly surprised by the",
    "The",
    "I highly recommend the",
    "Definitely one of the best",
    "The quality of the",
    "I keep coming back for the"
]


used_reviews = []


def generate_review():
    food = random.choice(food_items)
    quality = random.choice(qualities)
    starter = random.choice(review_starters)
    service = random.choice(service_phrases)

    patterns = [
        f"{starter} {food}. It was {quality} and absolutely hit the spot. {service}",
        f"{starter} {food} and it was {quality}. {service}",
        f"{starter} {food}—{quality}, fresh, and really satisfying. {service}",
        f"{starter} {food} and I couldn't fault it. It was {quality}. {service}",
        f"{starter} {food}, and the taste was {quality}. {service}"
    ]

    review = random.choice(patterns)

    if len(used_reviews) >= len(patterns) * len(food_items) * len(qualities):
        used_reviews.clear()

    while review in used_reviews:
        review = random.choice(patterns)

    used_reviews.append(review)
    return review


# config persistence and admin UI helper
def load_config():
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


@app.route("/")
def home():
    cfg = load_config()
    shop_name = cfg.get('shop_name', '')
    shop_url = cfg.get('shop_url', '')
    return render_template("index.html", google_url=GOOGLE_REVIEW_URL, shop_name=shop_name, shop_url=shop_url)

@app.route("/generate")
def generate():
    reviews = []
    while len(reviews) < 2:
        review = generate_review()
        if review not in reviews:
            reviews.append(review)

    return jsonify({
        "reviews": reviews,
        "google_url": GOOGLE_REVIEW_URL
    })


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    available_types = ["Fast Food", "Sea Food", "Desserts", "Vegetarian", "Asian", "Other"]
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        shop_url = request.form.get('shop_url', '').strip()
        quiz_types = request.form.getlist('quiz_types')
        cfg = {
            'shop_name': shop_name,
            'shop_url': shop_url,
            'quiz_types': quiz_types
        }
        save_config(cfg)
        return redirect(url_for('home'))

    cfg = load_config()
    return render_template('admin.html', cfg=cfg, available_types=available_types)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(host="0.0.0.0", port=port, debug=debug)