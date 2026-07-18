import json
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Download required NLTK data (quietly)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class FAQChatbot:
    def __init__(self, faq_file_path="faqs.json", threshold=0.3):
        self.threshold = threshold
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Load data
        self.faqs = []
        if os.path.exists(faq_file_path):
            with open(faq_file_path, 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
        else:
            print(f"Warning: {faq_file_path} not found.")
            
        self.questions = [faq['question'] for faq in self.faqs]
        self.answers = [faq['answer'] for faq in self.faqs]
        
        # Vectorizer setup
        self.vectorizer = TfidfVectorizer()
        if self.questions:
            preprocessed_questions = [self.preprocess(q) for q in self.questions]
            self.faq_matrix = self.vectorizer.fit_transform(preprocessed_questions)
        else:
            self.faq_matrix = None

    def preprocess(self, text):
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(word) 
            for word in tokens 
            if word not in self.stop_words
        ]
        return " ".join(processed_tokens)

    def get_best_answer(self, user_question):
        if self.faq_matrix is None or not self.questions:
            return "I have no knowledge base loaded."
            
        # Preprocess and vectorize user question
        processed_q = self.preprocess(user_question)
        user_vector = self.vectorizer.transform([processed_q])
        
        # Compute cosine similarity
        similarities = cosine_similarity(user_vector, self.faq_matrix)
        
        # Get highest similarity score and index
        best_match_idx = similarities.argmax()
        best_score = similarities[0][best_match_idx]
        
        if best_score < self.threshold:
            return "Sorry, I don't have an answer for that yet."
            
        return self.answers[best_match_idx]

# For testing independently
if __name__ == "__main__":
    bot = FAQChatbot()
    print("Bot initialized. Try a question: (e.g. 'How do I create an account?')")
    print(bot.get_best_answer("How do I create an account?"))
