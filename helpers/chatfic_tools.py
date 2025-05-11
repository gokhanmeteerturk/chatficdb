import json
from settings import SERVER_METADATA
from chatfic_validator import ChatficFormat, ChatficValidator, \
    ChatficValidationResult
import spacy
import nltk
from nltk.corpus import stopwords
import re
import joblib

def validate_storybasic_json(story_text: str, multimedia_list: list) -> ChatficValidationResult:
    validation_result = ChatficValidator.validate_json_text(
        json_text=story_text,
        chatfic_format=ChatficFormat.BASIC_JSON,
        multimedia_list=multimedia_list
    )
    return validation_result


def create_chatfic(story_text: str, story_key: str):

    input_data = json.loads(story_text)

    # Create the output data structure
    output_data = {
        "format": "chatficbasic",
        "version": "1.1",
        "chatFic": {
            "globalidentifier": story_key,
            "serverslug": SERVER_METADATA["slug"],
            "title": input_data["title"],
            "description": input_data["description"],
            "author": input_data["author"],
            "handles": input_data["handles"] if "handles" in input_data else {},
            "variables": input_data["variables"] if "variables" in input_data else {},
            "apps": input_data["apps"] if "apps" in input_data else {},
            "modified": input_data["modified"],
            "episode": input_data["episode"] if "episode" in input_data and input_data["episode"] else 1,
            "characters": input_data["characters"]
        },
        "bubble": []
    }

    for app_key, app_dict in output_data["chatFic"]["apps"].items():
        if "background" in app_dict:
            app_dict["background"] = app_dict["background"].replace("media/", "")

    # Initialize a message index counter
    message_index = 1
    pages = input_data["pages"]
    # Iterate through the pages and messages in the input data
    first_message_index_per_page = {}
    for page in pages:
        first_message_index_per_page[page["id"]]=message_index
        last_chatroom_in_page = ""
        for message in page["messages"]:
            last_chatroom_in_page=message["chatroom"] if "chatroom" in message else "-"
            bubble = {
                "messageindex": message_index,
                "message": message["message"],
                "from": message["from"],
                "side": int(message["side"]),
                "app": message["app"] if "app" in message else None,
                "chatroom": last_chatroom_in_page,
            }

            # Check if multimedia is not null in the input message
            if "multimedia" in message and message["multimedia"] is not None:
                bubble["multimedia"] = message["multimedia"].replace("media/","")
            if "extra" in message and message["extra"] is not None:
                bubble["extra"] = message["extra"]
            if "type" in message and message["type"] is not None:
                bubble["type"] = message["type"]

            output_data["bubble"].append(bubble)
            message_index += 1
        if "options" in page:
            options = page["options"]
            if options:
                if len(options) == 1:
                    temp_old_bubble = output_data["bubble"][-1]
                    output_data["bubble"][-1] = {
                        "messageindex": temp_old_bubble["messageindex"],
                        "message": temp_old_bubble["message"] if "message" in temp_old_bubble else None,
                        "options": [{"text":None,"to":options[0]["to"]}],
                        "from": temp_old_bubble["from"] if "from" in temp_old_bubble else None,
                        "side": temp_old_bubble["side"] if "side" in temp_old_bubble else 1,
                        "chatroom": temp_old_bubble["chatroom"] if "chatroom" in temp_old_bubble else last_chatroom_in_page,
                        "app":temp_old_bubble["app"]
                        }

                    if "multimedia" in temp_old_bubble and temp_old_bubble[
                        "multimedia"] is not None:
                        output_data["bubble"][-1]["multimedia"] = temp_old_bubble["multimedia"]
                    if "extra" in temp_old_bubble and temp_old_bubble[
                        "extra"] is not None:
                        output_data["bubble"][-1]["extra"] = temp_old_bubble["extra"]
                    if "type" in temp_old_bubble and temp_old_bubble[
                        "type"] is not None:
                        output_data["bubble"][-1]["type"] = temp_old_bubble["type"]
                elif len(options) > 0:
                    output_data["bubble"].append({
                        "messageindex": message_index,
                        "message": None,
                        "options": [{"text":option["message"],"to":option["to"]} for option in options],
                        "from": None,
                        "side": 1,
                        "chatroom": last_chatroom_in_page,
                        "app":None
                        })
                    message_index += 1

    # fix options: change page id to page["messages"][0]'s index.
    for message in output_data["bubble"]:
        if "options" in message and message["options"]:
            for option in message["options"]:
                option["to"] = first_message_index_per_page[option["to"]]

    # Return the output data:
    # json.dumps(output_data, indent=4, ensure_ascii=False)
    return output_data

class_dict = [
"angry",
"annoyed",
"crying",
"happy",
"naughty",
"neutral",
"sad",
"scared",
"shy",
"surprised",
]

stop_words = set(stopwords.words('english'))
nlp = spacy.load('en_core_web_sm')


production_model_logreg = joblib.load('database/sentiment_logreg.joblib')
production_vectorizer = joblib.load('database/sentiment_tfidf_vectorizer.joblib')

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

def analyze_sentiment_single(text: str):
    cleaned_text = preprocess_text(text)

    input_val = production_vectorizer.transform(
        [cleaned_text])

    prediction = production_model_logreg.predict(input_val)
    # print(f"For text: {text},\n  sentiment is: {class_dict[prediction[0]]}")
    return class_dict[prediction[0]]

def analyze_sentiment(compiled_story: dict):
    for bubble in compiled_story["bubble"]:
        if bubble["message"] and bubble["from"] and bubble["from"] not in [
            "player", "app"]:
            if "sentiment" in bubble:
                continue
            else:
                quick_check_emotion = quick_emotion(bubble["message"])
                if quick_check_emotion:
                    bubble["sentiment"] = quick_check_emotion
                else:
                    # print(f"Analyzing sentiment for message: {bubble['message']}")
                    bubble["sentiment"] = analyze_sentiment_single(bubble["message"])

    return compiled_story
emotion_dict = {
"🕛": 'neutral',
"🤐": 'neutral',
"🤑": 'happy',
"🤒": 'sad',
"🤓": 'happy',
"🤔": 'neutral',
"🤕": 'sad',
"🤗": 'happy',
"🤠": 'happy',
"🤡": 'happy',
"🤢": 'sad',
"🤧": 'sad',
"🤨": 'surprised',
"🤩": 'happy',
"🤪": 'naughty',
"🤫": 'happy',
"🤬": 'angry',
"🤮": 'sad',
"🤯": 'surprised',
"🥰": 'happy',
"🥳": 'happy',
"🥵": 'naughty',
"🥶": 'sad',
"🥺": 'sad',
"🧐": 'neutral',
"😀": 'happy',
"😁": 'happy',
"😂": 'happy',
"😅": 'happy',
"😇": 'happy',
"😉": 'naughty',
"😊": 'happy',
"😋": 'happy',
"😌": 'neutral',
"😍": 'happy',
"😎": 'naughty',
"😏": 'naughty',
"😐": 'annoyed',
"😑": 'annoyed',
"😓": 'sad',
"😔": 'sad',
"😖": 'sad',
"😗": 'neutral',
"😘": 'happy',
"😙": 'happy',
"😚": 'shy',
"😛": 'happy',
"😜": 'naughty',
"😝": 'happy',
"😞": 'sad',
"😠": 'angry',
"😡": 'angry',
"😈": 'naughty',
"👿": 'angry',
"😢": 'crying',
"😣": 'annoyed',
"😤": 'angry',
"😨": 'scared',
"😩": 'annoyed',
"😪": 'sad',
"😫": 'sad',
"😭": 'crying',
"😮": 'surprised',
"😯": 'surprised',
"😰": 'surprised',
"😱": 'scared',
"😲": 'surprised',
"😴": 'neutral',
"😵": 'surprised',
"🙃": 'happy',
"🙄": 'annoyed',
"😒": 'annoyed',
"cock": 'naughty',
"pussy": 'naughty',
"tits": 'naughty',
"horny": 'naughty',
"fuck me": 'naughty',
"fucked me": 'naughty',
"sexy": 'naughty',
"sucking": 'naughty',
"huge": 'naughty',
"omg": 'surprised',
"very sad":"sad",
"I'm afraid":"sad",
"haha":"happy",
"that's hot":"naughty",
"little slut":"naughty",
":)":"happy",
"wtf": 'annoyed',
"fuck you": 'angry'
}


def quick_emotion(sentence: str):
    for key, value in emotion_dict.items():
        if key in sentence:
            return value
    return None
