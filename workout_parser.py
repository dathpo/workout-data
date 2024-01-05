import os
import re
from datetime import datetime
from pathlib import Path
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot


class Session:
    def __init__(
        self, date, unprocessed_lines, weight=np.nan, body_fat=np.nan, exercises=np.nan
    ):
        self.date = date
        self.unprocessed_lines = unprocessed_lines
        self.body_fat = body_fat
        self.weight = weight
        self.exercises = exercises


class Set:
    def __init__(self, reps, form, rest_time):
        self.reps = reps
        self.form = form
        self.rest_time = rest_time


class Exercise:
    def __init__(self, exercise_type, variant, sets):
        self.type = exercise_type
        self.variant = variant
        self.sets = sets


def parse():
    with open(Path(os.getcwd()) / "workouts.txt", "r", encoding="utf-8") as file:
        return file.read()


def split_lines(data, multiplier):
    newline = "\n"
    return data.split(multiplier * newline)


def extract_session_dates(sessions_text, file_bytes):
    session_dates = [i[:8] for i in sessions_text]
    assert set(session_dates) == set(list_session_dates(file_bytes))
    for i, date in enumerate(session_dates):
        session_dates[i] = datetime.strptime(date, "%d/%m/%y").date()
    return session_dates, [
        Session(session_dates[i], sesh.split("\n", 1)[1:][0])
        for i, sesh in enumerate(sessions_text)
    ]


def list_session_dates(file_bytes):
    session_dates = [
        i[: i.index(":")] for i in file_bytes.split("\n") if "/" in i and ":" in i
    ]
    print(f"Number of workout sessions in file: {len(session_dates)}")
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


def extract_exercises(session):
    if session.unprocessed_lines != "":
        exercises_text_list = split_lines(session.unprocessed_lines, 2)
        # print("\nNEW (pre):", session.unprocessed_lines)
        # s = '- ring row parallel legs: 10 G, :55:28\n'
        print("exlist:", exercises_text_list)
        session_exercises = []
        exercise = Exercise
        session_exercises.append(exercise)
        for sets_list in exercises_text_list:
            print("setlist (pre):", sets_list)
            sets_list = split_lines(sets_list, 1)
            print("setlist (post):", sets_list)
            exercise_types = []
            for set_text in sets_list:
                exercise_type = re.search(r"(?<=- )(.*?)(?=[:,\n])", set_text)
                if exercise_type is not None:
                    exercise_types.append(exercise_type.group(0))
                    print("exercise type found: ", exercise_type.group(0))
                else:
                    print("exercise type not found: ", set_text)
            if len(exercise_types) > 0:
                assert len(set(exercise_types)) == 1
                print(f"exercise type: {exercise_type}")
                exercise.type = exercise_type.group(0)
        # print(result.group(1))
        # result = re.search(r"(?<=- )(.*?)(?=[:,\n])", s)
        # print("find: ", result.group(1))
        # print("\nNEW (post):", split_data)
        return session_exercises


def extract_body_fat(session):
    split_unprocessed_lines = session.unprocessed_lines.split("\n\n", 1)
    for i, line in enumerate(split_unprocessed_lines):
        if line.find("body fat") != -1:
            session.body_fat = float(line.split("\n")[-1].split()[-1][:-1])
            del split_unprocessed_lines[0]
    return session.body_fat


def plot(date_series, data_series, title, unit):
    sns.set()
    date_series = pd.Series(date_series[3:])
    data_series = pd.Series(data_series[3:])
    series_mask = np.isfinite(data_series)
    assert len(date_series) == len(data_series)
    pyplot.figure(figsize=(8, 6))
    ax = pyplot.gca()
    pyplot.xticks(rotation=45)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    pyplot.xlabel("Date")
    if len(data_series.dropna()) > 2:
        pyplot.yticks(np.arange(round(min(data_series)), max(data_series) + 1, 1))
    pyplot.ylabel(f"{title} ({unit})")
    pyplot.title(f"{title} History")
    pyplot.tight_layout()
    pyplot.plot(
        date_series[series_mask],
        data_series[series_mask],
        color="navy",
        linestyle="-",
        marker="o",
        markersize=4,
    )
    pyplot.show()


def main():
    file_data = parse()
    session_text_list = split_lines(
        file_data, 3
    )  # Three newline separators to separate sessions
    dates, sessions = extract_session_dates(session_text_list, file_data)
    weights = []
    body_fats = []
    exercises = []
    for s in sessions:
        weights.append(extract_weight(s))
        body_fats.append(extract_body_fat(s))
        exercises.append(extract_exercises(s))
        # print(s.date, s.weight)
    # plot(dates, weights, "Weight", "kg")
    # plot(dates, body_fats, "Body Fat", "%")


if __name__ == "__main__":
    main()
