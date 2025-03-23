import datetime
import re
import spacy
from huey import SqliteHuey
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
nlp = spacy.load('en_core_web_sm')

huey = SqliteHuey(filename="queue_db/huey_tasks.db")

def preprocess_text(text):
    # Convert text to lowercase
    text = text.lower()
    # Regex pattern to remove unwanted characters while preserving:
    # - Word characters (\w)
    # - Whitespace (\s)
    # - Emojis in the specified Unicode ranges
    pattern = r"[^\w\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251\U0000200D\u200B\U0001F004-\U0001F0CF]"
    # Substitute unwanted characters with an empty string
    text = re.sub(pattern, '', text)
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if token.text not in stop_words and not token.is_punct]
    return " ".join(tokens)


def analyze_sentiment(text: str):
    # Perform sentiment analysis
    return "Sentiment analysis successfully completed"


@huey.task()
def run_sentiment_analysis(story_id: int):
    story = "Hello, this is a great day! I am very happy!!!"
    result = analyze_sentiment(story)  # No return, just runs
    print(f"For story {story_id}: {result}")
