from people_also_ask.google import get_simple_answer, get_related_questions
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import hashlib

# crate create long tail keywords
def create_long_tail_keywords():

    print("Start building config")

    # import dataset
    df_plants = pd.read_csv("data/plants.csv")
    df_topics = pd.read_csv("data/topics.csv")
    df_queries = pd.read_csv("data/queries.csv")

    # build basic list of keywords
    keywords = []
    for index, topic in df_topics.iterrows():
        # join topic with plant name
        if "{PLANT_NAME}" in topic["topic"]:
            for index, plant in df_plants.iterrows():
                keywords.append(
                    {
                        "keyword": topic["topic"].replace("{PLANT_NAME}", plant["plant"]),
                        "synonyms": plant["synonyms"],
                    }
                )
        # use only topic
        else:
            keywords.append({"keyword": topic["topic"], "synonyms": topic["synonyms"]})

    print("Generated {} basic keywords".format(len(keywords)))

    # use google autocomplete for create alphabetic variation of keywords
    long_tail_keywords = []
    for index, keyword in keywords:

        print("{}/{} long tail keywords for: {}".format(index + 1, len(keywords), keyword["keyword"]))

        long_tail_keywords.append({"keyword": keyword["keyword"], "synonyms": keyword["synonyms"]})

        # foreach letter create query
        for letter in list("abcdefghijklmnopqrstuvwxyz"):
            resp = requests.get(
                "https://suggestqueries.google.com/complete/search?output=toolbar&hl=it&q={}+{}".format(
                    keyword["keyword"], letter
                ).replace(" ", "+")
            )
            xml = BeautifulSoup(resp.text, features="xml")
            suggestions = xml.find_all("suggestion")

            for suggestion in suggestions:
                long_tail_keywords.append(
                    {
                        "keyword": suggestion.attrs["data"],
                        "synonyms": keyword["synonyms"],
                    }
                )

            # prevent google blocking
            time.sleep(0.25)

        # save keywords dataframe
        df_queries = pd.concat([df_queries, pd.DataFrame(long_tail_keywords)])

        # remove duplicated rows
        df_queries = df_queries.drop_duplicates(keep="first")
        df_queries.to_csv("data/queries.csv", index=False)

    print("Generated {} long tail keywords".format(len(long_tail_keywords)))


# build qa database
def create_qa(size: 100):

    print("Start scraping")

    df_queries = pd.read_csv("data/queries.csv")
    df_qa = pd.read_csv("data/qa.csv")

    # get only the doesn't imported with size params
    df_queries_filtered = df_queries[df_queries["imported"] == False]
    df_queries_filtered = df_queries_filtered.head(size)
    index = 0

    for i, query in df_queries_filtered.iterrows():

        index = index + 1

        print("{}/{}: {}".format(index, size, query["question"]))

        # create some question from basic question
        for question in get_related_questions(query["question"], 5):
            # build qa dict and append to dataframe
            qa = get_qa(question, query["synonyms"])

            if qa:
                df_qa = pd.concat([df_qa, pd.DataFrame([qa])])

        # remove duplicated rows by id
        df_qa = df_qa.drop_duplicates(subset=["id"], keep="first")
        df_qa.to_csv("data/qa.csv", index=False)

        # set query as imported
        df_queries.loc[df_queries["question"] == query["question"], ["imported"]] = True
        df_queries.to_csv("data/queries.csv", index=False)

        time.sleep(1)


# retrive answer from question
def get_qa(question, synonyms):
    answer = get_simple_answer(question)
    synonyms = synonyms.split(",")
    tag = synonyms[0] if any(word in question for word in synonyms) or any(word in answer for word in synonyms) else ""

    # the unique id is used to avoid updating manually edited responses
    unique_id = hashlib.sha224(answer.encode("utf-8")).hexdigest()

    if not answer == "":
        return {"id": unique_id, "question": question, "answer": answer, "tag": tag}
    else:
        return None


# create markdown
def create_mds():

    print("Start building md")

    df_plants = pd.read_csv("data/plants.csv")
    df_qa = pd.read_csv("data/qa.csv")

    for index, plant in df_plants.iterrows():

        md = ""
        df_qa_filtered = df_qa[df_qa["tag"] == plant["plant"]]

        if not df_qa_filtered.empty:

            md += "---\n"
            md += "layout: article\n"
            md += "title: {}\n".format(plant["plant"].capitalize())
            md += "image: /images/{}.jpg\n".format(plant["plant"])
            md += "alt: pianta di {}\n".format(plant["plant"])
            md += "---\n\n"

            print("building md for: {}".format(plant["plant"]))

            for index, qa in df_qa_filtered.iterrows():
                md += "## {}\n\n".format(qa["question"])
                md += "{}\n\n".format(qa["answer"])

                # write markdown
                file = open("../articoli/{}.md".format(plant["plant"]), "w")
                file.write(md)
                file.close()
