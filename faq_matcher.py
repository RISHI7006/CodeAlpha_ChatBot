import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from nlp_processor import NLPProcessor

logger = logging.getLogger(__name__)

# Small-talk and conversational intent patterns
CONVERSATIONAL_INTENTS = {
    "greeting": {
        "patterns": ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"],
        "responses": [
            "Hello! I am your AI Support Assistant for TechNest. How can I assist you with your orders, returns, shipping, or products today?"
        ]
    },
    "goodbye": {
        "patterns": ["bye", "goodbye", "see you", "cya", "farewell", "have a nice day"],
        "responses": [
            "Goodbye! Thank you for contacting TechNest Support. Feel free to reach out anytime if you need more help!"
        ]
    },
    "thanks": {
        "patterns": ["thanks", "thank you", "thx", "appreciate it", "much appreciated", "awesome thanks"],
        "responses": [
            "You're very welcome! Let me know if there's anything else I can help you with."
        ]
    },
    "bot_identity": {
        "patterns": ["who are you", "what is your name", "what are you", "are you a bot", "are you human"],
        "responses": [
            "I'm TechNest FAQ Assistant, an intelligent customer support chatbot trained to answer your questions using Natural Language Processing (NLP) and semantic similarity matching!"
        ]
    },
    "help": {
        "patterns": ["help", "what can you do", "menu", "options", "commands"],
        "responses": [
            "I can assist you with:\n• Order tracking & cancellations\n• Returns, refunds & exchange policies\n• Shipping rates & international delivery\n• Accepted payment methods & security\n• Account settings, passwords & 2FA\n• Warranty claims & certified refurbished items\n\nJust type your question naturally, for example: 'How do I return an item?' or 'Can I track my shipment?'"
        ]
    }
}


class FAQMatcher:
    """
    NLP-driven FAQ Matching Engine using TF-IDF Vectorization,
    N-gram matching, and Cosine Similarity.
    """

    def __init__(
        self,
        faq_filepath: Optional[str] = "data/faqs.json",
        faqs: Optional[List[Dict[str, Any]]] = None,
        use_spacy: bool = False,
        similarity_threshold: float = 0.32
    ):
        self.nlp = NLPProcessor(use_spacy=use_spacy)
        self.similarity_threshold = similarity_threshold
        self.faqs: List[Dict[str, Any]] = []
        
        if faqs is not None:
            self.faqs = faqs
        elif faq_filepath:
            self.load_faqs(faq_filepath)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            norm='l2'
        )
        
        self.corpus_processed: List[str] = []
        self.tfidf_matrix = None
        self._fit_index()

    def load_faqs(self, filepath: str):
        """Loads FAQ questions, answers, and metadata from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
        except Exception as e:
            logger.error(f"Error loading FAQs from {filepath}: {e}")
            self.faqs = []

    def _fit_index(self):
        """Preprocesses FAQ questions and fits the TF-IDF vectorizer."""
        if not self.faqs:
            return

        # Augment questions with tags for richer semantic representation
        self.corpus_processed = []
        for faq in self.faqs:
            q_clean = self.nlp.preprocess(faq.get("question", ""))
            tags_clean = " ".join([self.nlp.preprocess(t) for t in faq.get("tags", [])])
            # Give question text primary weight
            combined = f"{q_clean} {q_clean} {tags_clean}".strip()
            self.corpus_processed.append(combined)

        if self.corpus_processed:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_processed)

    def check_conversational_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Checks if input matches greetings, farewells, or identity queries."""
        cleaned = self.nlp.clean_text(user_input).strip()
        tokens = [t.lower() for t in self.nlp.tokenize(user_input)]
        
        for intent, data in CONVERSATIONAL_INTENTS.items():
            for pattern in data["patterns"]:
                if cleaned == pattern or pattern in cleaned.split():
                    return {
                        "is_conversational": True,
                        "intent": intent,
                        "answer": data["responses"][0],
                        "confidence": 1.0,
                        "matched_question": pattern.title()
                    }
        return None

    def match_question(self, user_query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Matches a user query against the FAQ corpus using TF-IDF and Cosine Similarity.
        Returns the top answer, similarity score, confidence level, and suggested questions.
        """
        if not user_query or not user_query.strip():
            return {
                "matched": False,
                "answer": "Please ask a question so I can assist you!",
                "score": 0.0,
                "confidence_level": "none",
                "matched_faq": None,
                "top_matches": [],
                "suggestions": []
            }

        # 1. Check conversational intents first (Hi, Bye, Help, etc.)
        conv_intent = self.check_conversational_intent(user_query)
        if conv_intent:
            return {
                "matched": True,
                "is_conversational": True,
                "intent": conv_intent["intent"],
                "answer": conv_intent["answer"],
                "score": 1.0,
                "confidence_level": "high",
                "matched_faq": {
                    "question": conv_intent["matched_question"],
                    "category": "General",
                    "answer": conv_intent["answer"]
                },
                "top_matches": [],
                "suggestions": [
                    "How can I track my order?",
                    "What is your return policy?",
                    "What payment methods do you accept?"
                ]
            }

        # 2. Preprocess user query
        processed_query = self.nlp.preprocess(user_query)
        
        # If preprocessing stripped everything (e.g. all punctuation or stop words), try cleaned text
        if not processed_query.strip():
            processed_query = self.nlp.clean_text(user_query)

        if not self.corpus_processed or self.tfidf_matrix is None:
            return {
                "matched": False,
                "answer": "No FAQ database is currently loaded.",
                "score": 0.0,
                "confidence_level": "none",
                "matched_faq": None,
                "top_matches": [],
                "suggestions": []
            }

        # 3. Vectorize user query and compute Cosine Similarity
        query_vec = self.vectorizer.transform([processed_query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # 4. Keyword & Tag overlap boost
        user_tokens = set(self.nlp.preprocess_to_tokens(user_query))
        boosted_scores = np.copy(similarities)
        
        for idx, faq in enumerate(self.faqs):
            # Check question tokens overlap
            faq_tokens = set(self.nlp.preprocess_to_tokens(faq.get("question", "")))
            if user_tokens and faq_tokens:
                jaccard = len(user_tokens.intersection(faq_tokens)) / len(user_tokens.union(faq_tokens))
                boosted_scores[idx] += 0.15 * jaccard

            # Tag overlap bonus
            tags = [t.lower() for t in faq.get("tags", [])]
            for token in user_tokens:
                if token in tags:
                    boosted_scores[idx] += 0.14
                # Substring match in multi-word tags (e.g., 'shipment' in 'shipping')
                elif any(token in t or t in token for t in tags):
                    boosted_scores[idx] += 0.08

        # Clip scores to [0.0, 1.0]
        boosted_scores = np.clip(boosted_scores, 0.0, 1.0)

        # 5. Rank matches
        ranked_indices = np.argsort(boosted_scores)[::-1]
        best_idx = int(ranked_indices[0])
        best_score = float(boosted_scores[best_idx])
        best_faq = self.faqs[best_idx]

        # Collect top K matches
        top_matches = []
        for i in range(min(top_k, len(ranked_indices))):
            idx = int(ranked_indices[i])
            top_matches.append({
                "faq": self.faqs[idx],
                "score": round(float(boosted_scores[idx]), 4),
                "raw_cosine": round(float(similarities[idx]), 4)
            })

        # Suggestions for alternate exploration
        suggestions = [
            m["faq"]["question"]
            for m in top_matches[1:top_k]
            if m["faq"]["question"] != best_faq["question"]
        ]

        # If best match is strong (>= 0.55)
        if best_score >= 0.55:
            confidence_level = "high"
            answer = best_faq["answer"]
            matched = True
        # If moderate match (threshold <= score < 0.55)
        elif best_score >= self.similarity_threshold:
            confidence_level = "medium"
            answer = f"{best_faq['answer']}\n\n*(Matched question: **\"{best_faq['question']}\"**)*"
            matched = True
        # If low / no match (< threshold)
        else:
            confidence_level = "low"
            matched = False
            top_suggs = "\n".join([f"• {m['faq']['question']}" for m in top_matches[:3]])
            answer = (
                "I'm sorry, I couldn't find an exact answer to your question. "
                "Here are some related topics you might find helpful:\n\n"
                f"{top_suggs}\n\n"
                "You can also contact our 24/7 human support at support@technest.example.com or 1-800-555-TECH."
            )

        return {
            "matched": matched,
            "is_conversational": False,
            "answer": answer,
            "score": round(best_score, 4),
            "raw_cosine": round(float(similarities[best_idx]), 4),
            "confidence_level": confidence_level,
            "matched_faq": best_faq,
            "top_matches": top_matches,
            "suggestions": suggestions,
            "processed_query": processed_query
        }
