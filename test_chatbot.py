import unittest
from nlp_processor import NLPProcessor
from faq_matcher import FAQMatcher
from chatbot import FAQChatbot

class TestFAQChatbot(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.nlp = NLPProcessor()
        cls.bot = FAQChatbot()

    def test_text_cleaning(self):
        raw = "What's the status of my order??? Visit https://example.com!"
        cleaned = self.nlp.clean_text(raw)
        self.assertNotIn("?", cleaned)
        self.assertNotIn("https", cleaned)
        self.assertIn("what is", cleaned.lower())

    def test_tokenization(self):
        text = "How do I return a damaged product?"
        tokens = self.nlp.tokenize(text)
        self.assertIsInstance(tokens, list)
        self.assertTrue(len(tokens) > 0)
        self.assertIn("return", tokens)

    def test_stopword_removal_and_lemmatization(self):
        text = "Customers are requesting refunds for delayed packages"
        tokens = self.nlp.preprocess_to_tokens(text)
        # "refunds" should be lemmatized to "refund"
        # "delayed" or "packages" should be normalized
        self.assertTrue(any("refund" in t for t in tokens))
        self.assertTrue(any("package" in t for t in tokens))

    def test_conversational_greetings(self):
        greetings = ["hello", "hi", "hey there", "good morning"]
        for g in greetings:
            res = self.bot.get_response(g)
            self.assertTrue(res.get("is_conversational", False))
            self.assertIn("TechNest", res["answer"])

    def test_exact_match(self):
        query = "How can I track my order?"
        res = self.bot.get_response(query)
        self.assertEqual(res["confidence_level"], "high")
        self.assertEqual(res["matched_faq"]["id"], 1)

    def test_paraphrase_tracking(self):
        queries = [
            "where is my shipment",
            "track parcel location",
            "can you track my package"
        ]
        for q in queries:
            res = self.bot.get_response(q)
            self.assertIn(res["matched_faq"]["id"], [1, 3], f"Failed for query: {q}")
            self.assertIn(res["confidence_level"], ["high", "medium"])

    def test_paraphrase_refund(self):
        queries = [
            "how to send back an item and get money back",
            "what is the return policy",
            "how many days do i have to return something"
        ]
        for q in queries:
            res = self.bot.get_response(q)
            self.assertIn(res["matched_faq"]["id"], [4, 5, 6], f"Failed for query: {q}")

    def test_payment_methods(self):
        query = "do you take apple pay or paypal"
        res = self.bot.get_response(query)
        self.assertEqual(res["matched_faq"]["id"], 10)
        self.assertIn(res["confidence_level"], ["high", "medium"])

    def test_out_of_domain_query(self):
        query = "What is the capital of Australia?"
        res = self.bot.get_response(query)
        self.assertEqual(res["confidence_level"], "low")
        self.assertFalse(res["matched"])
        self.assertIn("couldn't find an exact answer", res["answer"])

if __name__ == "__main__":
    unittest.main()
