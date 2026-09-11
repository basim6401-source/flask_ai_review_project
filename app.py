from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from functools import wraps
import random
import os
import json
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Deployment-safe defaults
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Keep local dev behavior clean without hiding app functionality.
logging.getLogger("werkzeug").setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

GOOGLE_REVIEW_URL = "https://search.google.com/local/writereview?placeid=ChIJEb5DJgBDvDsRixDy-RGkGCw"

# Default available quiz types and mapping to food pools
AVAILABLE_TYPES = [
    "Fast Food",
    "Sea Food",
    "Desserts",
    "Vegetarian",
    "South Indian Vegetarian",
    "North Indian Vegetarian",
    "Biryani Shop",
    "Dry Indian Snacks",
    "Punjabi",
    "Chinese",
    "Italian",
    "Mughlai",
    "Dental Clinic",
    "Salon",
    "Spa",
    "Gym",
    "Auto Garage",
    "Hospital",
    "Real Estate",
    "Asian",
    "Other"
]

# Category-specific food items to better tailor reviews per quiz type
CATEGORY_FOODS = {
    "Fast Food": ["burger", "fries", "chicken sandwich", "milkshake", "loaded fries", "wrap"],
    "Sea Food": ["grilled fish", "prawn curry", "fried shrimp", "calamari", "fish and chips"],
    "Desserts": ["cheesecake", "ice cream", "chocolate lava cake", "brownie", "fruit tart"],
    "Vegetarian": ["veg burger", "salad", "paneer wrap", "veggie taco", "grilled vegetables"],
    "South Indian Vegetarian": ["masala dosa", "idli", "sambar vada", "ghee roast", "medu vada", "pongal"],
    "North Indian Vegetarian": ["paneer tikka", "dal makhani", "chole bhature", "aloo gobi", "vegetable biryani", "naan"],
    "Biryani Shop": ["chicken biryani", "mutton biryani", "veg biryani", "dum biryani", "hyderabadi biryani", "egg biryani"],
    "Dry Indian Snacks": ["samosa", "kachori", "sev puri", "pakora", "bhajji", "masala peanuts", "murukku", "chana chaat"],
    "Punjabi": ["paneer butter masala", "dal makhani", "butter naan", "amritsari chole", "tandoori roti", "sarson da saag"],
    "Chinese": ["dragon chicken", "fried rice", "spring rolls", "noodles", "manchurian", "dumplings"],
    "Italian": ["margherita pizza", "pasta alfredo", "lasagna", "garlic bread", "risotto", "pesto pasta"],
    "Mughlai": ["butter chicken", "dal murgh", "seekh kebab", "naan", "biryani", "shahi paneer"],
    "Dental Clinic": ["cleaning", "smile consultation", "root canal treatment", "teeth whitening", "check-up", "polishing"],
    "Salon": ["haircut", "hair spa", "facial", "coloring", "styling", "threading"],
    "Spa": ["massage therapy", "body spa", "facial treatment", "steam session", "aromatherapy", "pedicure"],
    "Gym": ["workout session", "trainer guidance", "strength training", "yoga class", "cardio zone", "fitness plan"],
    "Auto Garage": ["engine service", "wheel alignment", "oil change", "brake check", "car wash", "tyre service"],
    "Hospital": ["doctor consultation", "nursing care", "lab test", "emergency support", "check-up", "diagnostic scan"],
    "Real Estate": ["property visit", "site tour", "broker assistance", "villa viewing", "loan guidance", "apartment tour"],
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
    "Service was quick, the team was welcoming, and everything was handled professionally.",
    "Everything was efficient, organised, and the customer service was genuinely great.",
    "The place was clean, the staff were polite, and the process was handled perfectly.",
    "The service was outstanding and made the visit even more enjoyable."
]

service_type_phrases = {
    "Dental Clinic": [
        "The clinic was clean, the staff were professional, and the treatment was handled carefully.",
        "The visit felt smooth and reassuring from start to finish.",
        "The care provided was thoughtful, precise, and genuinely reassuring.",
        "Everything felt organised and comfortable, and the team made the process easy."
    ],
    "Salon": [
        "The salon was tidy, the team was friendly, and the styling was done with care.",
        "The service was smooth, professional, and the result looked exactly as expected.",
        "Everything felt polished and comfortable, and the attention to detail was excellent.",
        "The staff were welcoming and the treatment was delivered with real care."
    ],
    "Spa": [
        "The spa environment felt calming and the treatment was relaxing from start to finish.",
        "The service was gentle, professional, and the whole experience felt premium.",
        "Everything was clean, peaceful, and the care was truly personal.",
        "The team made the treatment feel comfortable, thoughtful, and restorative."
    ],
    "Gym": [
        "The trainers were supportive, knowledgeable, and made the session motivating.",
        "The atmosphere felt energetic and professional, and the guidance was helpful.",
        "The gym was well maintained, and the coaching made the workout feel effective.",
        "Everything felt organised and encouraging, and the support was excellent."
    ],
    "Auto Garage": [
        "The garage team was honest, efficient, and very professional with the service.",
        "The process was smooth, transparent, and the work was done with care.",
        "The staff explained everything clearly, and the service felt dependable.",
        "The repair and maintenance work was handled neatly and professionally."
    ],
    "Hospital": [
        "The staff were compassionate, efficient, and the care felt reassuring.",
        "The visit was organised, the team was helpful, and the support felt professional.",
        "The treatment and guidance were clear, calm, and genuinely supportive.",
        "Everything felt carefully managed and the medical attention was trustworthy."
    ],
    "Real Estate": [
        "The team was knowledgeable, respectful, and very helpful throughout the process.",
        "The property visit was smooth, informative, and the guidance felt transparent.",
        "Everything was explained clearly and the service felt reliable and professional.",
        "The experience was well organised and made the decision-making process easy."
    ]
}

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


def get_quality_words_for_type(qtype):
    if qtype in {"Dental Clinic", "Salon", "Spa", "Gym", "Auto Garage", "Hospital", "Real Estate"}:
        return [
            "professional",
            "smooth",
            "reliable",
            "excellent",
            "careful",
            "well-managed",
            "friendly",
            "high quality",
            "very reassuring",
            "genuinely impressive"
        ]
    return qualities


def generate_review_for_type(qtype=None):
    qtype = qtype or "Fast Food"
    pool = CATEGORY_FOODS.get(qtype, food_items)
    item = random.choice(pool)
    quality = random.choice(get_quality_words_for_type(qtype))
    service = random.choice(service_type_phrases.get(qtype, service_phrases))

    if qtype in {"Dental Clinic", "Salon", "Spa", "Gym", "Auto Garage", "Hospital", "Real Estate"}:
        starters = [
            f"The {qtype} experience was",
            f"I was impressed with the {qtype} service and the",
            f"The team at the {qtype} made the",
            f"The {qtype} here was"
        ]
        patterns = [
            f"{random.choice(starters)} {item}. It was {quality} and the attention to detail was excellent. {service}",
            f"{random.choice(starters)} {item}, and the service was {quality}. {service}",
            f"{random.choice(starters)} {item}. The process was smooth, professional, and genuinely reassuring. {service}",
            f"{random.choice(starters)} {item}, and I could tell the team cared about quality and comfort. {service}"
        ]
        return random.choice(patterns)

    starter = random.choice(review_starters)
    patterns = [
        f"{starter} {item}. It was {quality} and absolutely hit the spot. {service}",
        f"{starter} {item} and it was {quality}. {service}",
        f"{starter} {item}. It was {quality}, fresh, and really satisfying. {service}",
        f"{starter} {item} and I couldn't fault it. It was {quality}. {service}",
        f"{starter} {item}, and the taste was {quality}. {service}"
    ]
    return random.choice(patterns)


def generate_review():
    return generate_review_for_type()


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


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))


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
        review = generate_review_for_type(qtype)
        if review not in reviews:
            reviews.append(review)

    return jsonify({
        "reviews": reviews,
        "google_url": GOOGLE_REVIEW_URL,
        "type": qtype or ""
    })


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    available_types = [
        "Fast Food",
        "Sea Food",
        "Desserts",
        "Vegetarian",
        "South Indian Vegetarian",
        "North Indian Vegetarian",
        "Biryani Shop",
        "Dry Indian Snacks",
        "Punjabi",
        "Chinese",
        "Italian",
        "Mughlai",
        "Dental Clinic",
        "Salon",
        "Spa",
        "Gym",
        "Auto Garage",
        "Hospital",
        "Real Estate",
        "Asian",
        "Other"
    ]
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
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)