from flask import Flask, render_template, jsonify, request, redirect, url_for
import random
import os
import json

app = Flask(__name__)

GOOGLE_REVIEW_URL = "https://search.google.com/local/writereview?placeid=ChIJEb5DJgBDvDsRixDy-RGkGCw"

# Default available quiz types and mapping to food pools
AVAILABLE_TYPES = ["Fast Food", "Sea Food", "Desserts", "Vegetarian", "Asian", "Other"]

# Category-specific food items to better tailor reviews per quiz type
CATEGORY_FOODS = {
    "Fast Food": ["burger", "fries", "chicken sandwich", "milkshake", "loaded fries", "wrap"],
    "Sea Food": ["grilled fish", "prawn curry", "fried shrimp", "calamari", "fish and chips"],
    "Desserts": ["cheesecake", "ice cream", "chocolate lava cake", "brownie", "fruit tart"],
    "Vegetarian": ["veg burger", "salad", "paneer wrap", "veggie taco", "grilled vegetables"],
    "Asian": ["sushi", "ramen", "pad thai", "dumplings", "fried rice"],
}

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
    shops = cfg.get('shops', [])
    # legacy support: if single shop keys exist, include them
    if not shops:
        shop_name = cfg.get('shop_name', '')
        shop_url = cfg.get('shop_url', '')
        if shop_name or shop_url:
            shops = [{'name': shop_name, 'url': shop_url}]

    # provide available quiz types to the frontend
    quiz_types = cfg.get('quiz_types', AVAILABLE_TYPES)

    return render_template("index.html", google_url=GOOGLE_REVIEW_URL, shops=shops, available_types=quiz_types)

@app.route("/generate")
def generate():
    # Optional quiz type filter via query param
    qtype = request.args.get('type')

    # load config to read available quiz types
    cfg = load_config()
    available = cfg.get('quiz_types', AVAILABLE_TYPES)

    # if no type provided, default to first admin-selected type (if any)
    if not qtype and available:
        qtype = available[0]

    # select food pool based on quiz type; fall back to default pool
    if qtype and qtype in CATEGORY_FOODS:
        pool = CATEGORY_FOODS[qtype]
    else:
        pool = food_items

    reviews = []
    while len(reviews) < 2:
        # generate a review using the selected pool
        food = random.choice(pool)
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
        if review not in reviews:
            reviews.append(review)

    return jsonify({
        "reviews": reviews,
        "google_url": GOOGLE_REVIEW_URL,
        "type": qtype or ""
    })


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    available_types = ["Fast Food", "Sea Food", "Desserts", "Vegetarian", "Asian", "Other"]
    if request.method == 'POST':
        names = request.form.getlist('shop_name')
        urls = request.form.getlist('shop_url')
        shops = []
        for n, u in zip(names, urls):
            n = n.strip()
            u = u.strip()
            if n or u:
                shops.append({'name': n, 'url': u})
        quiz_types = request.form.getlist('quiz_types')
        cfg = {
            'shops': shops,
            'quiz_types': quiz_types
        }
        save_config(cfg)
        return redirect(url_for('home'))

    cfg = load_config()
    # ensure legacy keys are handled
    if 'shops' not in cfg:
        shop_name = cfg.get('shop_name', '')
        shop_url = cfg.get('shop_url', '')
        cfg['shops'] = []
        if shop_name or shop_url:
            cfg['shops'].append({'name': shop_name, 'url': shop_url})
    return render_template('admin.html', cfg=cfg, available_types=available_types)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(host="0.0.0.0", port=port, debug=debug)