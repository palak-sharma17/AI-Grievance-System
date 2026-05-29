"""
AI classifier for grievance department detection and sentiment analysis.
Trains a TF-IDF + Naive Bayes model on bangalore_dataset.csv at startup.
"""
import os
import re
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

# ── Department → CategoryEnum mapping ─────────────────────────────────────────
DEPT_TO_CATEGORY = {
    "Electricity":    "electricity",
    "Transport":      "transport",
    "Public Safety":  "safety",
    "Sanitation":     "sanitation",
    "Roads":          "road",
    "Water":          "water",
}

DEPT_TO_DEPARTMENT = {
    "Electricity":    "Electricity Department",
    "Transport":      "Transport Authority",
    "Public Safety":  "Police & Safety Dept",
    "Sanitation":     "Sanitation & Waste Dept",
    "Roads":          "Roads & Infrastructure Dept",
    "Water":          "Water Supply Board",
}

SENTIMENT_MAP = {
    "Positive": "positive",
    "Negative": "negative",
    "Critical": "critical",
}

PRIORITY_MAP = {
    "Positive": "low",
    "Negative": "medium",
    "Critical": "critical",
}


def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.strip()


class GrievanceClassifier:
    def __init__(self):
        self.dept_pipeline: Pipeline = None
        self.sent_pipeline: Pipeline = None
        self.trained = False

    def train(self, csv_path: str = "bangalore_dataset.csv"):
        """Train both department and sentiment classifiers."""
        if not os.path.exists(csv_path):
            print(f"[AI] Dataset not found at {csv_path}. Using rule-based fallback.")
            return

        df = pd.read_csv(csv_path)
        df["clean_text"] = df["text"].apply(_clean)

        # Department classifier
        self.dept_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            ("clf",   MultinomialNB(alpha=0.5)),
        ])
        self.dept_pipeline.fit(df["clean_text"], df["department"])

        # Sentiment classifier
        self.sent_pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            ("clf",   MultinomialNB(alpha=0.5)),
        ])
        self.sent_pipeline.fit(df["clean_text"], df["sentiment"])

        self.trained = True
        print(f"[AI] Classifier trained on {len(df)} samples.")

    def predict(self, text: str) -> dict:
        """
        Returns:
            category    : CategoryEnum value string
            department  : human-readable dept name
            ai_sentiment: 'positive' | 'negative' | 'critical'
            priority    : PriorityEnum value string
            ai_confidence: float 0-1
        """
        clean = _clean(text)

        if self.trained:
            # Department
            dept_proba = self.dept_pipeline.predict_proba([clean])[0]
            dept_label = self.dept_pipeline.classes_[np.argmax(dept_proba)]
            confidence = float(np.max(dept_proba))

            # Sentiment
            sent_label = self.sent_pipeline.predict([clean])[0]
        else:
            dept_label, confidence, sent_label = self._rule_based(text)

        category   = DEPT_TO_CATEGORY.get(dept_label, "other")
        department = DEPT_TO_DEPARTMENT.get(dept_label, "General Administration")
        sentiment  = SENTIMENT_MAP.get(sent_label, "negative")
        priority   = PRIORITY_MAP.get(sent_label, "medium")

        return {
            "category":     category,
            "department":   department,
            "ai_sentiment": sentiment,
            "priority":     priority,
            "ai_confidence": round(confidence, 3),
        }

    def _rule_based(self, text: str) -> tuple:
        """Fallback when dataset not available."""
        t = text.lower()
        if any(w in t for w in ["water", "pipe", "leak", "flood", "drain"]):
            return "Water", 0.75, "Negative"
        if any(w in t for w in ["road", "pothole", "bridge", "footpath"]):
            return "Roads", 0.75, "Negative"
        if any(w in t for w in ["garbage", "waste", "sewage", "sanitation", "toilet"]):
            return "Sanitation", 0.75, "Negative"
        if any(w in t for w in ["electricity", "power", "light", "transformer"]):
            return "Electricity", 0.75, "Negative"
        if any(w in t for w in ["police", "crime", "theft", "safety", "security"]):
            return "Public Safety", 0.75, "Critical"
        if any(w in t for w in ["bus", "transport", "traffic", "signal"]):
            return "Transport", 0.75, "Negative"
        return "Sanitation", 0.5, "Negative"


# Singleton instance
classifier = GrievanceClassifier()