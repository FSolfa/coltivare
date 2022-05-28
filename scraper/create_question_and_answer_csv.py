# we have override this unmaintained package for bug fix
from people_also_ask.google import get_simple_answer, get_related_questions, search
from utils import get_dataset, wait_seconds
import pandas as pd
import hashlib

MAX_RELATED_QUESTION = 5
DELEY_IN_SECONDS = 30

# Create question and answer csv for eg.
# How to grow tomato from seed?
# You can grow...
def create_question_and_answer_csv():
    _, _, df_keywords, df_question_answer = get_dataset()

    # skip already imported keywords
    df_keywords = df_keywords[df_keywords["imported"] == False]

    for i, keyword in df_keywords.iterrows():

        current_keyword = keyword["keyword"]
        current_subject = keyword["subject"]

        print("Keyword: {}".format(current_keyword))

        # create question from basic keywords
        for question in get_related_questions(current_keyword, MAX_RELATED_QUESTION):

            print("{}".format(question))

            # build qa dict and append to dataframe
            question_answer = get_question_and_answer(question, current_subject)

            if question_answer:
                df_question_answer = pd.concat([df_question_answer, pd.DataFrame([question_answer])])

            wait_seconds(DELEY_IN_SECONDS)

        # remove duplicated rows by id
        df_question_answer = df_question_answer.drop_duplicates(subset=["id"], keep="first")
        df_question_answer.to_csv("data/qa.csv", index=False)

        # set query as imported
        df_keywords.loc[df_keywords["keyword"] == current_keyword, ["imported"]] = True
        df_keywords.to_csv("data/queries.csv", index=False)

        print("\n")
        wait_seconds(DELEY_IN_SECONDS)

    print("All data imported!!")


# retrive answer from question
def get_question_and_answer(question, subject):
    # use people also ask package
    answer = get_simple_answer(question)

    # the unique id is used to avoid updating manually edited responses
    unique_id = hashlib.sha224(answer.encode("utf-8")).hexdigest()

    if not answer == "":
        return {"id": unique_id, "question": question, "answer": answer, "subject": subject}
    else:
        return None


# export question and answer csv to xlsx
def question_and_answer_from_csv_to_xlsx():
    _, _, df_keywords, _ = get_dataset()

    # save to xlsx for google translation
    df_keywords.to_excel("data/queries.xlsx")


create_question_and_answer_csv()
