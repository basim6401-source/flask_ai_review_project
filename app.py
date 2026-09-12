from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from functools import wraps
import random
import os
import json
import logging
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Deployment-safe defaults
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Keep local dev behavior clean without hiding app functionality.
logging.getLogger("werkzeug").setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)

ADMIN_USERNAME = "huzaifa"
ADMIN_PASSWORD = "admin123"
ADMIN_FIRST_NAME = "Huzaifa"
ADMIN_PATH = os.environ.get("ADMIN_PATH", "/huzaifa-admin").rstrip("/") or "/huzaifa-admin"

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
    "Bike Garage",
    "Super Bike Garage",
    "Juice Shop",
    "Medical Shop",
    "Grocery Shop",
    "Mens Clothing",
    "Woman Traditional Wear",
    "Tire Shop",
    "Toys Shop",
    "Kids Clothing",
    "Ladies PG",
    "Gents PG",
    "Hotel",
    "School",
    "Hostel",
    "Mobile Shop",
    "Footwear Shop",
    "Mens Salon",
    "Auto Spare Parts Shop",
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
    "Bike Garage": ["bike service", "chain lubrication", "brake tuning", "wheel balancing", "engine check", "bike wash"],
    "Super Bike Garage": ["superbike tuning", "performance check", "bike detailing", "engine tune-up", "suspension setup", "helmet fitting"],
    "Juice Shop": ["mango juice", "fresh lime", "fruit smoothie", "banana shake", "apple juice", "coconut water"],
    "Medical Shop": ["vitamin tablets", "pain relief", "first aid kit", "health supplement", "cold medicine", "blood pressure check"],
    "Grocery Shop": ["fresh vegetables", "daily essentials", "milk packets", "rice sacks", "seasonal fruits", "household items"],
    "Mens Clothing": ["shirts", "denim jeans", "formal trousers", "hoodies", "casual jackets", "perfume set"],
    "Woman Traditional Wear": ["saree", "lehenga", "salwar set", "dupatta", "anarkali", "traditional blouse"],
    "Tire Shop": ["tyre replacement", "wheel balancing", "puncture repair", "alignment check", "tubeless fitting", "pressure adjustment"],
    "Toys Shop": ["remote car", "puzzle set", "soft toy", "learning blocks", "board game", "kids bicycle"],
    "Kids Clothing": ["school uniform", "t-shirt set", "winter jacket", "kids hoodie", "denim shorts", "play dress"],
    "Ladies PG": ["room stay", "clean room", "shared kitchen", "security support", "laundry service", "comfortable stay"],
    "Gents PG": ["room stay", "clean room", "shared kitchen", "security support", "laundry service", "comfortable stay"],
    "Hotel": ["room stay", "breakfast service", "clean room", "front desk support", "comfortable stay", "housekeeping"],
    "School": ["classroom environment", "teacher guidance", "school support", "friendly staff", "clean campus", "student care"],
    "Hostel": ["shared room", "clean washroom", "safe stay", "mess service", "study space", "supportive staff"],
    "Mobile Shop": ["phone display", "screen protector", "phone case", "battery replacement", "mobile accessories", "network setup"],
    "Footwear Shop": ["sports shoes", "formal shoes", "sandals", "slippers", "comfort fit", "shoe sizing"],
    "Mens Salon": ["beard trim", "haircut", "facial", "grooming service", "styling", "clean shave"],
    "Auto Spare Parts Shop": ["engine parts", "brake pads", "spark plug", "gear parts", "oil filter", "battery service"],
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
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')


def normalize_quiz_types(types):
    selected = []
    seen = set()
    for item in (types or []):
        if isinstance(item, str):
            item = item.strip()
        if item and item not in seen:
            selected.append(item)
            seen.add(item)
    return selected


def parse_custom_quiz_types(raw_value):
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        raw_value = raw_value.splitlines()
    values = []
    for item in raw_value:
        if not isinstance(item, str):
            continue
        for chunk in item.split(','):
            chunk = chunk.strip()
            if chunk:
                values.append(chunk)
    return values


def normalize_shop_types(shop):
    if isinstance(shop.get('types'), list):
        values = shop.get('types', [])
    elif isinstance(shop.get('type'), list):
        values = shop.get('type', [])
    elif shop.get('type'):
        values = [shop.get('type')]
    else:
        values = []
    clean = []
    seen = set()
    for item in values:
        if isinstance(item, str):
            item = item.strip()
        if item and item not in seen:
            clean.append(item)
            seen.add(item)
    return clean


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT,
            business_type TEXT,
            types TEXT DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute(
        """
        INSERT OR IGNORE INTO admins
            (username, password_hash, first_name, last_name, phone)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), ADMIN_FIRST_NAME, "", "")
    )
    conn.commit()

    columns = [row['name'] for row in conn.execute("PRAGMA table_info(businesses)").fetchall()]
    if 'types' not in columns:
        conn.execute("ALTER TABLE businesses ADD COLUMN types TEXT DEFAULT '[]'")

    shop_count = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
    if shop_count == 0:
        cfg = load_config_from_file()
        for shop in cfg.get('shops', []):
            types = normalize_shop_types(shop)
            primary_type = types[0] if types else (shop.get('type') or '')
            conn.execute(
                "INSERT INTO businesses (name, url, business_type, types) VALUES (?, ?, ?, ?)",
                (shop.get('name', ''), shop.get('url', ''), primary_type, json.dumps(types, ensure_ascii=False))
            )

    type_count = conn.execute("SELECT COUNT(*) FROM quiz_types").fetchone()[0]
    cfg = load_config_from_file()
    if type_count and cfg.get('quiz_types') == []:
        conn.execute('DELETE FROM quiz_types')
        type_count = 0
    if type_count == 0:
        types = cfg.get('quiz_types', [])
        for t in types:
            conn.execute("INSERT INTO quiz_types (name) VALUES (?)", (t,))

    conn.commit()
    conn.close()


def load_config_from_file():
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def load_config():
    init_db()
    conn = get_db_connection()
    shops = []
    for row in conn.execute(
        "SELECT name, url, business_type, types FROM businesses ORDER BY id"
    ).fetchall():
        types = []
        raw_types = row['types']
        if raw_types:
            try:
                parsed = json.loads(raw_types)
                if isinstance(parsed, list):
                    types = parsed
            except Exception:
                types = []
        if not types and row['business_type']:
            types = [row['business_type']]
        primary_type = types[0] if types else (row['business_type'] or '')
        shops.append({
            'name': row['name'],
            'url': row['url'],
            'type': primary_type,
            'types': types,
        })
    quiz_types = [
        row['name'] for row in conn.execute("SELECT name FROM quiz_types ORDER BY id").fetchall()
    ]
    conn.close()

    normalized = normalize_quiz_types(quiz_types)

    if not shops and not normalized:
        cfg = load_config_from_file()
        if cfg:
            save_config(cfg)
            return cfg
        return {'shops': [], 'quiz_types': AVAILABLE_TYPES}

    return {'shops': shops, 'quiz_types': normalized}


def save_config(cfg):
    init_db()
    normalized_shops = []
    for shop in cfg.get('shops', []):
        types = normalize_shop_types(shop)
        primary_type = types[0] if types else (shop.get('type') or '')
        normalized_shops.append({
            'name': shop.get('name', ''),
            'url': shop.get('url', ''),
            'type': primary_type,
            'types': types,
        })

    normalized_cfg = {
        'shops': normalized_shops,
        'quiz_types': normalize_quiz_types(cfg.get('quiz_types'))
    }
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump(normalized_cfg, f, ensure_ascii=False, indent=2)

    conn = get_db_connection()
    conn.execute('DELETE FROM businesses')
    conn.execute('DELETE FROM quiz_types')
    for shop in normalized_cfg.get('shops', []):
        types = normalize_shop_types(shop)
        primary_type = types[0] if types else (shop.get('type') or '')
        conn.execute(
            'INSERT INTO businesses (name, url, business_type, types) VALUES (?, ?, ?, ?)',
            (shop.get('name', ''), shop.get('url', ''), primary_type, json.dumps(types, ensure_ascii=False))
        )
    for t in normalized_cfg.get('quiz_types', []):
        conn.execute('INSERT INTO quiz_types (name) VALUES (?)', (t,))
    conn.commit()
    conn.close()


def get_admin(username):
    conn = get_db_connection()
    admin = conn.execute(
        "SELECT id, username, password_hash, first_name, last_name, phone "
        "FROM admins WHERE username = ? AND is_active = 1",
        (username,)
    ).fetchone()
    conn.close()
    return admin


def list_admins():
    conn = get_db_connection()
    admins = conn.execute(
        "SELECT id, username, first_name, last_name, phone "
        "FROM admins WHERE is_active = 1 ORDER BY id"
    ).fetchall()
    conn.close()
    return admins


def create_admin(username, password, first_name, last_name, phone):
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO admins (username, password_hash, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, generate_password_hash(password), first_name, last_name, phone)
        )
        conn.commit()
    finally:
        conn.close()


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
        admin = get_admin(username)
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin['username']
            session['admin_profile'] = {
                'first_name': admin['first_name'],
                'last_name': admin['last_name'],
                'phone': admin['phone'],
            }
            return redirect(url_for('admin'))
        error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_profile', None)
    return redirect(url_for('login'))


@app.route("/")
def home():
    cfg = load_config()
    shops = cfg.get('shops', [])
    if not shops:
        shop_name = cfg.get('shop_name', '')
        shop_url = cfg.get('shop_url', '')
        if shop_name or shop_url:
            shops = [{'name': shop_name, 'url': shop_url, 'type': ''}]
    for shop in shops:
        shop.setdefault('type', '')

    quiz_types = normalize_quiz_types(cfg.get('quiz_types'))
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


@app.route(ADMIN_PATH, methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        names = request.form.getlist('shop_name')
        urls = request.form.getlist('shop_url')
        shop_types = {}
        for key, values in request.form.lists():
            if key.startswith('shop_type_'):
                index = key.split('_', 2)[2]
                shop_types.setdefault(index, [])
                shop_types[index].extend(values)

        shops = []
        for i, (n, u) in enumerate(zip(names, urls)):
            n = n.strip()
            u = u.strip()
            selected_types = []
            for item in shop_types.get(str(i), []):
                item = item.strip()
                if item:
                    selected_types.append(item)
            if not selected_types:
                legacy_types = request.form.getlist('shop_type')
                if i < len(legacy_types):
                    selected_types = [legacy_types[i].strip()]
            if n or u or selected_types:
                primary = selected_types[0] if selected_types else ''
                shops.append({'name': n, 'url': u, 'type': primary, 'types': selected_types})

        custom_quiz_types = parse_custom_quiz_types(request.form.get('custom_quiz_types'))
        quiz_types = request.form.getlist('quiz_types') + custom_quiz_types
        cfg = {
            'shops': shops,
            'quiz_types': normalize_quiz_types(quiz_types)
        }
        save_config(cfg)
        return redirect(url_for('home'))

    cfg = load_config()
    cfg['quiz_types'] = normalize_quiz_types(cfg.get('quiz_types'))
    if 'shops' not in cfg:
        shop_name = cfg.get('shop_name', '')
        shop_url = cfg.get('shop_url', '')
        cfg['shops'] = []
        if shop_name or shop_url:
            cfg['shops'].append({'name': shop_name, 'url': shop_url, 'type': '', 'types': []})
    for shop in cfg.get('shops', []):
        shop.setdefault('type', '')
        shop.setdefault('types', normalize_shop_types(shop))
    available_types = normalize_quiz_types(AVAILABLE_TYPES + cfg.get('quiz_types', []))
    return render_template(
        'admin.html',
        cfg=cfg,
        available_types=available_types,
        admins=list_admins(),
        admin_message=request.args.get('admin_message'),
        admin_error=request.args.get('admin_error')
    )


@app.route(f'{ADMIN_PATH}/admins', methods=['POST'])
@login_required
def add_admin():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not all([username, password, first_name, last_name, phone]):
        return redirect(url_for('admin', admin_error='All admin fields are required.'))
    if username == ADMIN_USERNAME:
        return redirect(url_for('admin', admin_error='The owner account is already reserved.'))

    try:
        create_admin(username, password, first_name, last_name, phone)
    except sqlite3.IntegrityError:
        return redirect(url_for('admin', admin_error='That username already has admin access.'))

    return redirect(url_for('admin', admin_message='Admin access granted.'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = True
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=True)