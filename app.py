import os
import json
from flask import Flask, render_template, request, jsonify
from chatbot import FAQChatbot
from nlp_processor import NLPProcessor

app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize default bot
bot = FAQChatbot()

@app.route("/")
def index():
    """Renders the main chat UI."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint to process user messages."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Optional dynamic threshold
    threshold = data.get("threshold")
    if threshold is not None:
        try:
            bot.matcher.similarity_threshold = float(threshold)
        except ValueError:
            pass

    response = bot.get_response(message)
    # Also attach NLP preprocessing breakdown for visual transparency
    nlp_steps = bot.nlp.get_preprocessing_steps(message)
    response["nlp_pipeline"] = nlp_steps

    return jsonify(response)

@app.route("/api/preprocess", methods=["POST"])
def preprocess_text():
    """Inspect text preprocessing steps for educational/debugging purposes."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    steps = bot.nlp.get_preprocessing_steps(text)
    return jsonify(steps)

@app.route("/api/faqs", methods=["GET"])
def get_faqs():
    """Returns all FAQs grouped by category."""
    grouped = bot.get_all_faqs()
    return jsonify({
        "total": len(bot.matcher.faqs),
        "categories": grouped
    })

@app.route("/api/add_faq", methods=["POST"])
def add_faq():
    """Adds a new FAQ to the live dataset."""
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    category = data.get("category", "General").strip()
    tags = data.get("tags", [])

    if not question or not answer:
        return jsonify({"error": "Question and answer are required."}), 400

    new_faq = {
        "id": len(bot.matcher.faqs) + 1,
        "category": category,
        "question": question,
        "answer": answer,
        "tags": tags if isinstance(tags, list) else [t.strip() for t in str(tags).split(",") if t.strip()]
    }

    bot.matcher.faqs.append(new_faq)
    bot.matcher._fit_index()

    # Also persist to file if possible
    try:
        faq_file = os.path.join(os.path.dirname(__file__), "data", "faqs.json")
        with open(faq_file, "w", encoding="utf-8") as f:
            json.dump(bot.matcher.faqs, f, indent=2)
    except Exception as e:
        app.logger.warning(f"Failed to persist new FAQ to disk: {e}")

    return jsonify({"success": True, "faq": new_faq})

if __name__ == "__main__":
    print("🚀 Starting TechNest FAQ Chatbot Web Server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
