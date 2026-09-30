# 🤖 TechNest FAQ Chatbot (NLP-Powered)

An intelligent customer support FAQ Chatbot built using **Natural Language Processing (NLP)**, **TF-IDF Vectorization**, and **Cosine Similarity**. 

This system satisfies all requirements of **Task 2: Chatbot for FAQs**:
- ✅ **FAQ Dataset**: Rich, categorized dataset of frequently asked questions and answers covering an e-commerce & tech support platform.
- ✅ **NLP Preprocessing**: Tokenization, cleaning, contraction expansion, stopword filtering, and POS-aware lemmatization using **NLTK** (with SpaCy support).
- ✅ **Semantic Matching**: Cosine similarity matching powered by TF-IDF matrices (unigrams & bigrams), with intent detection and tag-based lexical overlap boosting.
- ✅ **Best Matching Response**: Confidence-scored answers (High, Medium, Low) with suggestions and fallback handling.
- ✅ **Interactive Interfaces**:
  1. **Modern Web Chat UI (Flask + HTML5/CSS3/JS)** with live NLP inspection drawer, dark/light theme, and dynamic category filters.
  2. **Streamlit Application (`streamlit_app.py`)** with real-time similarity threshold sliders and vector breakdown.
  3. **Interactive Command-Line Interface (CLI)** (`python chatbot.py`) with debug inspection mode.

---

## 📂 Project Structure

```
d:\DOWNLOAD\ChatBot\
├── data/
│   └── faqs.json               # 25+ categorized FAQ questions, answers, and tags
├── nlp_processor.py            # Tokenization, cleaning, stopword removal, lemmatization
├── faq_matcher.py              # TF-IDF vectorizer, Cosine Similarity, intent handler
├── chatbot.py                  # Main Chatbot controller & interactive terminal CLI
├── app.py                      # Flask REST API and web server
├── streamlit_app.py            # Streamlit dashboard and chat UI
├── templates/
│   └── index.html              # Modern responsive chat interface
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphism dark/light UI styling
│   └── js/
│       └── chat.js             # Client messaging & live NLP inspector logic
├── test_chatbot.py             # Automated unit tests
├── requirements.txt            # Project dependencies
└── README.md                   # Documentation and usage guide
```

---

## 🧠 NLP & Similarity Matching Pipeline

### 1. Text Preprocessing (`nlp_processor.py`)
1. **Contraction Expansion**: Expands phrases like *"what's"* $\rightarrow$ *"what is"*, *"can't"* $\rightarrow$ *"cannot"*.
2. **Cleaning & Normalization**: Strips URLs, punctuation, and special symbols, and converts text to lower case.
3. **Tokenization**: Uses `nltk.tokenize.word_tokenize` to split queries into constituent words.
4. **Stopword Filtering**: Removes high-frequency grammatical filler words (using NLTK's English stop words corpus).
5. **POS-Aware Lemmatization**: Uses `nltk.stem.WordNetLemmatizer` with Part-of-Speech tagging (`averaged_perceptron_tagger`) so verbs and nouns are reduced to root lemmas (e.g., *"tracking"* $\rightarrow$ *"track"*, *"refunds"* $\rightarrow$ *"refund"*, *"delivered"* $\rightarrow$ *"deliver"*).

### 2. FAQ Semantic Matching (`faq_matcher.py`)
- **TF-IDF Vectorizer**: Constructs a term-frequency inverse-document-frequency matrix incorporating unigrams and bigrams (`ngram_range=(1, 2)`).
- **Cosine Similarity**: Measures the directional similarity between user query vector $\vec{q}$ and FAQ vectors $\vec{d}$:
  $$\text{Cosine Similarity}(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\|_2 \|\vec{d}\|_2}$$
- **Intent & Tag Boosting**: Short queries (e.g., *"my shipment"*, *"return"*) receive lexical overlap bonuses to avoid under-matching.
- **Conversational Intents**: Handles greetings (*"hi"*, *"good morning"*), goodbyes (*"bye"*), bot identity, and help menus gracefully without false FAQ matching.

### 3. Confidence Thresholding
- 🟢 **High Confidence ($\ge 0.55$)**: Direct answer displayed immediately.
- 🟡 **Medium Confidence ($0.30 - 0.55$)**: Answer displayed with *"Matched question: ... "* and suggested related questions.
- 🔴 **Low Confidence ($< 0.30$)**: Polite fallback indicating no close match, with top-3 suggested alternative topics and human agent contact info.

---

## 🚀 How to Run

### 1. Prerequisites & Installation
Ensure Python 3.10+ is installed:
```bash
pip install -r requirements.txt
```

### 2. Run the Interactive Web UI (Flask)
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

**Features:**
- Real-time chat bubbles with bot and user avatars.
- **Live NLP Inspector drawer** showing original query $\rightarrow$ cleaned text $\rightarrow$ tokenization $\rightarrow$ stopwords removed $\rightarrow$ lemmatized tokens $\rightarrow$ cosine score.
- Dynamic threshold slider to adjust matching sensitivity live.
- Dark mode & Light mode toggle.
- Category browser for one-click exploration of topics.

### 3. Run the Streamlit UI
```bash
streamlit run streamlit_app.py
```
Provides an interactive dashboard to test queries, adjust threshold sliders, and inspect JSON vector parameters.

### 4. Run the Terminal CLI
```bash
python chatbot.py
```
- Type any question directly:
  ```text
  You 👤: How can I track my shipment?
  Bot 🤖 [HIGH CONFIDENCE: 89.2%]:
  You can track your order by navigating to 'My Orders' in your account dashboard and clicking 'Track Order'...
  ```
- Type `debug <question>` to inspect the NLP pipeline tokens in terminal.
- Type `categories` to view all FAQ topics.
- Type `exit` or `quit` to leave.

### 5. Run the Automated Tests
```bash
python test_chatbot.py
```
Runs 9 comprehensive unit tests covering preprocessing, tokenization, lemmatization, exact matches, paraphrasing, and out-of-domain detection.

---

## 📊 Sample Queries to Test

| Query | Expected Matched FAQ / Intent | Confidence |
| :--- | :--- | :--- |
| `"Hello!"` | Conversational Greeting | High (100%) |
| `"How can I track my order?"` | Order Tracking | High (>85%) |
| `"where is my parcel"` | Order Tracking (Paraphrased) | High/Medium |
| `"What is the return policy?"` | Returns & Refunds Policy | High (>80%) |
| `"do you take apple pay or paypal"` | Payment Methods | High (>75%) |
| `"can I ship to an APO military address?"`| Shipping & Delivery | High (>80%) |
| `"What is the capital of Australia?"` | Out-of-domain query | Low (Fallback) |
