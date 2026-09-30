import re
import string
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Attempt to import and set up NLTK
_NLTK_AVAILABLE = False
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import wordnet
    
    # Try downloading required datasets silently
    for resource in ["punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]:
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            pass
    _NLTK_AVAILABLE = True
except Exception as e:
    logger.warning(f"NLTK setup warning: {e}")

# Attempt to check SpaCy availability
_SPACY_AVAILABLE = False
_SPACY_NLP = None
try:
    import spacy
    _SPACY_AVAILABLE = True
    try:
        _SPACY_NLP = spacy.load("en_core_web_sm")
    except Exception:
        # Model might not be downloaded yet
        _SPACY_NLP = None
except Exception:
    _SPACY_AVAILABLE = False


# Contraction expansion dictionary for robust cleaning
CONTRACTIONS = {
    "can't": "cannot",
    "won't": "will not",
    "n't": " not",
    "'re": " are",
    "'s": " is",
    "'d": " would",
    "'ll": " will",
    "'t": " not",
    "'ve": " have",
    "'m": " am",
    "how's": "how is",
    "what's": "what is",
    "where's": "where is",
    "it's": "it is",
    "there's": "there is",
    "i'm": "i am",
    "you're": "you are"
}

# Default standard fallback stop words in case NLTK corpus is not downloaded
FALLBACK_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "could", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "i",
    "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same",
    "she", "should", "so", "some", "such", "t", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with",
    "you", "your", "yours", "yourself", "yourselves"
}

# In question answering, question words often carry useful context, but can also dilute FAQ matching.
# We retain key domain words and provide clean options.

class NLPProcessor:
    """
    NLP preprocessing pipeline using NLTK or SpaCy.
    Handles tokenization, normalization, punctuation removal,
    stopword filtering, and lemmatization.
    """

    def __init__(self, use_spacy: bool = False, remove_stopwords: bool = True):
        self.use_spacy = use_spacy and (_SPACY_NLP is not None)
        self.remove_stopwords = remove_stopwords
        
        # Initialize Stopwords
        self.stop_words = set()
        if _NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
            except Exception:
                self.stop_words = set(FALLBACK_STOPWORDS)
        else:
            self.stop_words = set(FALLBACK_STOPWORDS)
            
        # Initialize Lemmatizer
        self.lemmatizer = None
        if _NLTK_AVAILABLE:
            try:
                self.lemmatizer = WordNetLemmatizer()
            except Exception:
                self.lemmatizer = None

    def expand_contractions(self, text: str) -> str:
        """Expands common English contractions."""
        text = text.lower()
        for contraction, expansion in CONTRACTIONS.items():
            text = text.replace(contraction, expansion)
        return text

    def clean_text(self, text: str) -> str:
        """
        Cleans text: expands contractions, removes URLs, punctuation,
        and normalizes whitespaces.
        """
        if not text:
            return ""
        text = self.expand_contractions(text)
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        # Remove special characters / punctuation but keep spaces and alphanumeric
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _get_wordnet_pos(self, treebank_tag: str):
        """Maps TreeBank POS tag to WordNet POS tag for accurate lemmatization."""
        if not _NLTK_AVAILABLE:
            return None
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    def tokenize(self, text: str) -> List[str]:
        """Tokenizes text using NLTK word_tokenize or regex fallback."""
        if not text:
            return []
        cleaned = self.clean_text(text)
        if _NLTK_AVAILABLE:
            try:
                return word_tokenize(cleaned)
            except Exception:
                return cleaned.split()
        return re.findall(r'\b\w+\b', cleaned)

    def preprocess(self, text: str) -> str:
        """
        Full preprocessing pipeline returning processed string:
        clean -> tokenize -> filter stopwords -> lemmatize -> joined string.
        """
        tokens = self.preprocess_to_tokens(text)
        return " ".join(tokens)

    def preprocess_to_tokens(self, text: str) -> List[str]:
        """
        Pipeline returning list of processed token strings.
        """
        if not text or not text.strip():
            return []

        # SpaCy Branch (if enabled and model loaded)
        if self.use_spacy and _SPACY_NLP:
            doc = _SPACY_NLP(self.expand_contractions(text.lower()))
            processed = []
            for token in doc:
                if token.is_punct or token.is_space:
                    continue
                if self.remove_stopwords and token.is_stop:
                    continue
                lemma = token.lemma_.strip()
                if lemma:
                    processed.append(lemma)
            return processed

        # NLTK / Standard Pipeline
        tokens = self.tokenize(text)
        
        # Stopword filtering
        if self.remove_stopwords:
            tokens = [w for w in tokens if w.lower() not in self.stop_words and len(w) > 1]

        # Lemmatization
        if self.lemmatizer and _NLTK_AVAILABLE:
            try:
                pos_tags = nltk.pos_tag(tokens)
                lemmatized = []
                for word, tag in pos_tags:
                    pos = self._get_wordnet_pos(tag)
                    if pos:
                        lemmatized.append(self.lemmatizer.lemmatize(word, pos=pos))
                    else:
                        lemmatized.append(self.lemmatizer.lemmatize(word))
                tokens = lemmatized
            except Exception:
                tokens = [self.lemmatizer.lemmatize(w) for w in tokens]

        return tokens

    def get_preprocessing_steps(self, text: str) -> Dict[str, Any]:
        """
        Returns step-by-step breakdown of text transformation.
        Useful for education, demonstration, and UI inspection.
        """
        original = text
        cleaned = self.clean_text(text)
        tokens = self.tokenize(text)
        without_stopwords = [w for w in tokens if w.lower() not in self.stop_words]
        lemmatized = self.preprocess_to_tokens(text)
        
        return {
            "original": original,
            "cleaned": cleaned,
            "tokens": tokens,
            "stopwords_removed": without_stopwords,
            "lemmatized_tokens": lemmatized,
            "final_processed_text": " ".join(lemmatized)
        }
