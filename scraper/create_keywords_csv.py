from utils import get_dataset, wait_seconds
import pandas as pd
import requests
from bs4 import BeautifulSoup

DELEY_IN_SECONDS = 1

# Create list of long tail keywords
# eg. how to grow tomatoes from seed
def create_keywords_csv():
    # build keywords
    df_keywords = create_keywords()

    # set Nan to false, remove duplicated rows and save file
    df_keywords = df_keywords.fillna(False)
    df_keywords = df_keywords.drop_duplicates(subset=["keyword"], keep="first")
    df_keywords.to_csv("data/keywords.csv", index=False)


# Create list of long tail keywords
# eg. how to grow tomatoes from seed
def create_keywords():
    _, _, df_keywords, _ = get_dataset()

    # build basic list of keywords
    keywords = build_product_from_topics_and_subject()

    # use google autocomplete for create alphabetic variation of keywords
    keywords = generate_keywords_variation_with_google_autosuggest(keywords)

    # add keywords dataframe
    df_keywords = pd.concat([df_keywords, pd.DataFrame(keywords)])

    return df_keywords


# create product from topic and subject
# eg. grow tomato, grow flower, grow ...
def build_product_from_topics_and_subject():
    df_subject, df_topics, _, _ = get_dataset()
    return [
        {"keyword": "{} {}".format(topic, subject), "subject": subject}
        for topic in df_topics["topic"]
        for subject in df_subject["subject"]
    ]


# create long tail keyword using google autosuggest
def generate_keywords_variation_with_google_autosuggest(base_keywords):
    keywords = []
    autosuggest_url = "https://suggestqueries.google.com/complete/search?output=toolbar&hl=it&q={}+{}"

    for keyword in base_keywords:

        current_keyword = keyword["keyword"]
        current_subject = keyword["subject"]

        print("Generate long tail keywords for: {}".format(current_keyword))

        keywords.append({"keyword": current_keyword, "subject": current_subject})

        # foreach letter create query
        for letter in list("abcdefghijklmnopqrstuvwxyz"):
            # request query to google
            resp = requests.get(autosuggest_url.format(current_keyword, letter).replace(" ", "+"))
            xml = BeautifulSoup(resp.text, features="xml")

            # parse google response
            suggestions = xml.find_all("suggestion")
            keywords = keywords + [
                {"keyword": suggestion.attrs["data"], "subject": current_subject} for suggestion in suggestions
            ]

        # prevent google blocking with small sleep
        wait_seconds(DELEY_IN_SECONDS)

    return keywords


# start here
create_keywords_csv()
