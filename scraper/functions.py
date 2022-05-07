from people_also_ask.google import get_simple_answer, get_related_questions, search
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import sys
import hashlib
from urllib import parse
from datetime import date


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
            time.sleep(1)

        # save keywords dataframe
        df_queries = pd.concat([df_queries, pd.DataFrame(long_tail_keywords)])

        # remove duplicated rows
        df_queries = df_queries.drop_duplicates(keep="last")
        df_queries.to_csv("data/queries.csv", index=False)

    print("Generated {} long tail keywords".format(len(long_tail_keywords)))


# build qa database
def create_qa():

    df_queries = pd.read_csv("data/queries.csv")
    df_qa = pd.read_csv("data/qa.csv")

    # get only the doesn't imported with size params
    df_queries_filtered = df_queries[df_queries["imported"] == False]

    for i, query in df_queries_filtered.iterrows():

        j = 0

        print("------- {} -------".format(query["question"]))

        # create some question from basic question
        for question in get_related_questions(query["question"], 5):

            j = j + 1

            print("{}/5: {}".format(j, question))

            # build qa dict and append to dataframe
            qa = get_qa(question, query["synonyms"])

            if qa:
                df_qa = pd.concat([df_qa, pd.DataFrame([qa])])

            wait(30)

        # remove duplicated rows by id
        df_qa = df_qa.drop_duplicates(subset=["id"], keep="first")
        df_qa.to_csv("data/qa.csv", index=False)

        # set query as imported
        df_queries.loc[df_queries["question"] == query["question"], ["imported"]] = True
        df_queries.to_csv("data/queries.csv", index=False)

        print("\n")
        wait(60)

    print("All data imported!!")


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
            today = date.today()

            # correct space before plant name
            if "’" not in plant["articles"]:
                plant["articles"] = plant["articles"] + " "

            md += "---\n"
            md += "layout: article\n"
            md += "title: Come coltivare e prendersi cura {}{}\n".format(plant["articles"], plant["plant"].capitalize())
            md += "description: Tutte le cure necessarie, irrigazioni, terreno, consigli e molto altro sulla coltivazione {}{}\n".format(
                plant["articles"], plant["plant"].capitalize()
            )
            md += "plant_name: {}\n".format(plant["plant"].capitalize())
            md += "image: /images/{}.jpg\n".format(plant["plant"].replace(" ", "-"))
            md += "alt: pianta di {}\n".format(plant["plant"])
            md += "date: 2022-01-01\n"
            md += "last_modified_at: {}\n".format(today.strftime("%Y-%m-%d"))
            md += "---\n\n"

            print("building md for: {}".format(plant["plant"]))

            for index, qa in df_qa_filtered.iterrows():
                md += "## {}\n\n".format(qa["question"])

                youtube = get_youtube_video_id(qa["answer"])

                if youtube:
                    md += '<iframe width="100%" height="315" src="https://www.youtube.com/embed/{}" title="{}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n\n'.format(
                        youtube[0], qa["question"]
                    )
                else:
                    md += "{}\n\n".format(qa["answer"])

                # write markdown
                file = open("../articoli/{}.md".format(plant["plant"]), "w")
                file.write(md)
                file.close()


# check if url is youtube video
def get_youtube_video_id(url):
    url_parsed = parse.urlparse(url)
    qsl = parse.parse_qs(url_parsed.query)
    return qsl.get("v")


# process wait for prevent blocking
def wait(wating_time):
    sys.stdout.write("\r")
    for remaining in range(wating_time, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("Waiting {:2d} seconds remaining.".format(remaining))
        sys.stdout.flush()
        time.sleep(1)

    sys.stdout.write("\r")
