import pandas as pd
import sys
import time

# Read and return list of pandas dataset
def get_dataset():
    df_subject = pd.read_csv("data/subject.csv")
    df_topics = pd.read_csv("data/topics.csv")
    df_keywords = pd.read_csv("data/keywords.csv")
    df_question_answer = pd.read_csv("data/question_answer.csv")

    return df_subject, df_topics, df_keywords, df_question_answer


# process wait for prevent blocking
def wait_seconds(wating_time):
    sys.stdout.write("\r")
    for remaining in range(wating_time, 0, -1):
        sys.stdout.write("\r")
        sys.stdout.write("Waiting {:2d} seconds remaining.".format(remaining))
        sys.stdout.flush()
        time.sleep(1)

    sys.stdout.write("\r")
