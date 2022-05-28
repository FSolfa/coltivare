import pandas as pd
from urllib import parse
from datetime import date

# TODO: refactior this

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
            md += "show_in_sidebar: {}\n".format(plant["show_in_sidebar"])
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
