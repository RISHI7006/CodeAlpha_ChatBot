import sys
import os
from typing import Dict, Any, Optional
from faq_matcher import FAQMatcher
from nlp_processor import NLPProcessor

class FAQChatbot:
    """
    Main Chatbot controller for handling user interactions,
    routing queries to the FAQMatcher, and formatting conversational output.
    """

    def __init__(self, faq_file: str = "data/faqs.json", similarity_threshold: float = 0.32, use_spacy: bool = False):
        self.nlp = NLPProcessor(use_spacy=use_spacy)
        self.matcher = FAQMatcher(
            faq_filepath=faq_file,
            use_spacy=use_spacy,
            similarity_threshold=similarity_threshold
        )
        self.conversation_history = []

    def get_response(self, user_input: str) -> Dict[str, Any]:
        """Processes user input and returns the response payload with metadata."""
        if not user_input or not user_input.strip():
            return {
                "answer": "Please type a question or choose from the suggested topics below.",
                "confidence_level": "none",
                "score": 0.0,
                "suggestions": [
                    "How can I track my order?",
                    "What is your return policy?",
                    "What payment methods do you accept?"
                ]
            }

        result = self.matcher.match_question(user_input)
        
        # Save to history
        self.conversation_history.append({
            "user": user_input,
            "bot": result["answer"],
            "score": result["score"],
            "confidence": result["confidence_level"]
        })

        return result

    def get_all_faqs(self):
        """Returns all FAQs grouped by category."""
        categories = {}
        for faq in self.matcher.faqs:
            cat = faq.get("category", "General")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(faq)
        return categories


def run_cli():
    """Runs an interactive command line interface for the chatbot."""
    print("=" * 65)
    print("  🤖 WELCOME TO TECHNEST SUPPORT FAQ CHATBOT (NLP-POWERED)")
    print("=" * 65)
    print("Powered by NLTK, TF-IDF Vectorization, and Cosine Similarity.")
    print("Commands:")
    print("  - Type any question naturally (e.g. 'How do I return a product?')")
    print("  - Type 'debug <question>' to see NLP tokenization & lemmatization details")
    print("  - Type 'categories' to list all FAQ topics")
    print("  - Type 'help' for options, or 'exit' / 'quit' to close")
    print("=" * 65)
    print()

    bot = FAQChatbot()

    while True:
        try:
            user_input = input("\nYou 👤: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nBot 🤖: Goodbye! Have a fantastic day!")
                break

            if user_input.lower() == "categories":
                print("\n📁 Available Categories:")
                cats = bot.get_all_faqs()
                for cat, faqs in cats.items():
                    print(f"  • {cat} ({len(faqs)} questions)")
                continue

            if user_input.lower().startswith("debug "):
                query = user_input[6:].strip()
                steps = bot.nlp.get_preprocessing_steps(query)
                print("\n🔬 --- NLP Preprocessing Inspection ---")
                print(f"  Original:             {steps['original']}")
                print(f"  Cleaned text:         {steps['cleaned']}")
                print(f"  Tokenized:            {steps['tokens']}")
                print(f"  Stopwords removed:    {steps['stopwords_removed']}")
                print(f"  Lemmatized tokens:    {steps['lemmatized_tokens']}")
                print(f"  Processed for TF-IDF: {steps['final_processed_text']}")
                print("---------------------------------------")
                result = bot.matcher.match_question(query)
                print(f"  Cosine Similarity:    {result.get('raw_cosine', 0.0)}")
                print(f"  Boosted Score:        {result.get('score', 0.0)} ({result['confidence_level'].upper()})")
                if result.get("matched_faq"):
                    print(f"  Matched FAQ:          {result['matched_faq']['question']}")
                print("---------------------------------------")
                continue

            res = bot.get_response(user_input)
            
            # Print response
            conf = res.get("confidence_level", "").upper()
            score = res.get("score", 0.0)
            
            if conf in ["HIGH", "MEDIUM"]:
                badge = f"[{conf} CONFIDENCE: {score:.1%}]"
            elif conf == "LOW":
                badge = f"[LOW MATCH: {score:.1%}]"
            else:
                badge = ""

            print(f"\nBot 🤖 {badge}:\n{res['answer']}")

            if res.get("suggestions") and res["confidence_level"] != "high":
                print("\n💡 Suggested questions:")
                for sugg in res["suggestions"][:3]:
                    print(f"   ➤ \"{sugg}\"")

        except (KeyboardInterrupt, EOFError):
            print("\n\nBot 🤖: Session ended. Goodbye!")
            break


if __name__ == "__main__":
    run_cli()
