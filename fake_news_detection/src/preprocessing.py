"""Text preprocessing: cleaning, tokenisation, stopword removal, stemming, lemmatization.

Uses NLTK when available (stopwords corpus, PorterStemmer, WordNetLemmatizer).
Each component falls back independently to an offline implementation if NLTK or
its data cannot be loaded, so the pipeline always runs.
"""
import re
from functools import lru_cache

from .fallback_nlp import FALLBACK_STOPWORDS, SimpleLemmatizer, SimpleStemmer

_URL = re.compile(r"https?://\S+|www\.\S+")
_EMAIL = re.compile(r"\S+@\S+\.\S+")
_HTML = re.compile(r"<[^>]+>")
_HANDLE = re.compile(r"[@#]\w+")
_SOURCE_TAG = re.compile(r"\((?:reuters|ap|afp)\)")
_TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")

# Words that reveal the *publisher* rather than the truthfulness of an article.
# Removing them stops models from "cheating" on datasets such as Kaggle's Fake/True.csv.
LEAKY_TOKENS = frozenset({"reuters", "ap", "afp"})


@lru_cache(maxsize=1)
def load_resources():
    """Return (stopwords, stemmer, lemmatizer, info) - NLTK if possible, else fallbacks."""
    info = {"stopwords": "built-in fallback", "stemmer": "built-in fallback",
            "lemmatizer": "built-in fallback"}
    stopwords, stemmer, lemmatizer = None, None, None
    try:
        import nltk
    except ImportError:
        nltk = None

    def attempt(fn, package):
        """Run fn; if NLTK data is missing try one download, then retry."""
        try:
            return fn()
        except LookupError:
            try:
                nltk.download(package, quiet=True)
                return fn()
            except Exception:
                return None
        except Exception:
            return None

    if nltk is not None:
        def _stemmer():
            from nltk.stem import PorterStemmer
            s = PorterStemmer()
            s.stem("running")
            return s

        def _stopwords():
            from nltk.corpus import stopwords as sw
            return set(sw.words("english"))

        def _lemmatizer():
            from nltk.stem import WordNetLemmatizer
            lem = WordNetLemmatizer()
            lem.lemmatize("cats")
            return lem

        try:
            stemmer = _stemmer()
        except Exception:
            stemmer = None
        stopwords = attempt(_stopwords, "stopwords")
        lemmatizer = attempt(_lemmatizer, "wordnet")
        if lemmatizer is None:  # newer NLTK versions may also need omw-1.4
            lemmatizer = attempt(_lemmatizer, "omw-1.4")

    if stopwords is not None:
        info["stopwords"] = "NLTK"
    else:
        stopwords = set(FALLBACK_STOPWORDS)
    if stemmer is not None:
        info["stemmer"] = "NLTK PorterStemmer"
    else:
        stemmer = SimpleStemmer()
    if lemmatizer is not None:
        info["lemmatizer"] = "NLTK WordNetLemmatizer"
    else:
        lemmatizer = SimpleLemmatizer()
    return frozenset(stopwords), stemmer, lemmatizer, info


def backend_info():
    """Which implementation is powering each preprocessing step."""
    return dict(load_resources()[3])


class TextPreprocessor:
    """Configurable text-cleaning pipeline.

    Steps: lowercase -> strip URLs/HTML/emails/handles -> tokenise (letters only)
           -> stopword removal -> lemmatization -> stemming -> join with spaces.
    """

    def __init__(self, remove_stopwords=True, stemming=False, lemmatization=True,
                 min_token_len=2, strip_leaky_tokens=True):
        self.remove_stopwords = remove_stopwords
        self.stemming = stemming
        self.lemmatization = lemmatization
        self.min_token_len = min_token_len
        self.strip_leaky_tokens = strip_leaky_tokens
        self._stopwords, self._stemmer, self._lemmatizer, _ = load_resources()
        self._cache = {}

    def config(self):
        """Constructor arguments - saved with the model so inference matches training."""
        return {"remove_stopwords": self.remove_stopwords, "stemming": self.stemming,
                "lemmatization": self.lemmatization,
                "min_token_len": self.min_token_len,
                "strip_leaky_tokens": self.strip_leaky_tokens}

    # ---- individual steps ------------------------------------------------
    def clean(self, text):
        text = str(text).lower().replace("\u2019", "'").replace("\u2018", "'")
        text = _HTML.sub(" ", text)
        text = _URL.sub(" ", text)
        text = _EMAIL.sub(" ", text)
        text = _HANDLE.sub(" ", text)
        text = _SOURCE_TAG.sub(" ", text) if self.strip_leaky_tokens else text
        return text

    def tokenize(self, text):
        return _TOKEN.findall(text)

    @staticmethod
    def _strip_apostrophe(token):
        if token.endswith("'s"):
            return token[:-2]
        return token.replace("'", "")

    def _normalise_token(self, token):
        if token in self._cache:
            return self._cache[token]
        out = token
        if self.lemmatization:
            out = self._lemmatizer.lemmatize(out)
        if self.stemming:
            out = self._stemmer.stem(out)
        self._cache[token] = out
        return out

    def process_tokens(self, tokens):
        result = []
        for raw in tokens:
            if self.remove_stopwords and raw in self._stopwords:
                continue
            tok = self._strip_apostrophe(raw)
            if len(tok) < self.min_token_len:
                continue
            if self.remove_stopwords and tok in self._stopwords:
                continue
            if self.strip_leaky_tokens and tok in LEAKY_TOKENS:
                continue
            tok = self._normalise_token(tok)
            if len(tok) >= self.min_token_len:
                result.append(tok)
        return result

    # ---- public API ----------------------------------------------------------
    def transform_one(self, text):
        return " ".join(self.process_tokens(self.tokenize(self.clean(text))))

    def transform(self, texts):
        return [self.transform_one(t) for t in texts]
