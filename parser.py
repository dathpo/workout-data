import os
from datetime import datetime, timedelta
import matplotlib.dates as mdates

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot


class Session:
    def __init__(self, date, unprocessed_lines, weight=np.nan, body_fat=np.nan, exercise=np.nan):
        self.date = date
        self.unprocessed_lines = unprocessed_lines
        self.body_fat = body_fat
        self.weight = weight
        self.exercise = exercise


class Set:
    def __init__(self, reps, form, rest_time):
        self.reps = reps
        self.form = form
        self.rest_time = rest_time


class Exercise:
    def __init__(self, exercise_type, sets):
        self.type = exercise_type
        self.sets = sets


def parse():
    with open(os.path.join(os.path.dirname(__file__), "workouts.txt")) as file:
        return file.read()


def extract_sessions(data, multiplier):
    newline = "\n"
    return data.split(multiplier * newline)


def extract_dates(sessions_text, file_bytes):
    session_dates = [i[:8] for i in sessions_text]
    assert set(session_dates) == set(list_session_dates(file_bytes))
    for i, date in enumerate(session_dates):
        session_dates[i] = datetime.strptime(date, "%d/%m/%y").date()
    return session_dates, [Session(session_dates[i], sesh.split("\n", 1)[1:][0]) for i, sesh in
                           enumerate(sessions_text)]


def list_session_dates(file_bytes):
    session_dates = [i[:i.index(":")] for i in file_bytes.split("\n") if "/" in i and ":" in i]
    print("Number of workout sessions in file: {}".format(len(session_dates)))
    return session_dates


def extract_weight(session):
    split_unprocessed_lines = session.unprocessed_lines.split("\n")
    for i, line in enumerate(split_unprocessed_lines):
        if line.find("weight") != -1:
            session.weight = float(line.split()[1])
            remainder_lines = session.unprocessed_lines.split("\n", 2)
            if len(remainder_lines) > 1:
                assert remainder_lines[1] == ""
                session.unprocessed_lines = remainder_lines[2:][0]
            else:
                session.unprocessed_lines = ""
            break
    return session.weight


def extract_exercise(session):
    pass


def extract_body_fat(session):
    split_unprocessed_lines = session.unprocessed_lines.split("\n\n", 1)
    for i, line in enumerate(split_unprocessed_lines):
        if line.find("body fat") != -1:
            session.body_fat = float(line.split("\n")[-1].split()[-1][:-1])
            del split_unprocessed_lines[0]
    return session.body_fat


def plot_weight_history(date_series, weight_series):
    sns.set()
    date_series = pd.Series(date_series[3:])
    weight_series = pd.Series(weight_series[3:])
    series_mask = np.isfinite(weight_series)
    assert len(date_series) == len(weight_series)
    pyplot.figure(figsize=(8, 6))
    ax = pyplot.gca()
    pyplot.xticks(rotation=45)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    pyplot.xlabel("Date")
    pyplot.yticks(np.arange(round(min(weight_series)), max(weight_series) + 1, 1))
    pyplot.ylabel("Weight (kg)")
    pyplot.title("Weight History")
    pyplot.tight_layout()
    pyplot.plot(date_series[series_mask], weight_series[series_mask], color='navy', linestyle='-', marker='o',
                markersize=4)
    pyplot.show()


if __name__ == "__main__":
    file_data = parse()
    session_text_list = extract_sessions(file_data, 3)
    dates, sessions = extract_dates(session_text_list, file_data)
    weights = []
    body_fat_list = []
    for s in sessions:
        weights.append(extract_weight(s))
        body_fat_list.append(extract_body_fat(s))
        # print(s.date, s.weight)
    plot_weight_history(dates, weights)
