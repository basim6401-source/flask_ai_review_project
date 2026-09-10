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


# config persistence removed; admin UI not included in this revert

@app.route("/")
def home():
    return render_template("index.html", google_url=GOOGLE_REVIEW_URL)

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


# Admin route removed in this revert


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(host="0.0.0.0", port=port, debug=debug)