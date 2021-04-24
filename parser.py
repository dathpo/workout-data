import os
from datetime import datetime


class Session:
    def __init__(self, date, unprocessed_lines, weight="NaN", exercise="NaN"):
        self.date = date
        self.unprocessed_lines = unprocessed_lines
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


def extract_sessions(file_bytes, multiplier):
    newline = "\n"
    session_text_list = file_bytes.split(multiplier * newline)
    return extract_date(session_text_list, file_bytes)


def extract_date(session_text_list, file_bytes):
    session_dates_from_split = [i[:8] for i in session_text_list]
    assert set(session_dates_from_split) == set(list_session_dates(file_bytes))
    return [Session(datetime.strptime(session_dates_from_split[i], "%d/%m/%y").date(), sesh) for i, sesh in
            enumerate(session_text_list)]


def list_session_dates(file_bytes):
    session_dates = [i[:i.index(":")] for i in file_bytes.split("\n") if "/" in i and ":" in i]
    print("Number of workout sessions in file: {}".format(len(session_dates)))
    return session_dates


def extract_weight(session):
    pass


def extract_exercise(session):
    pass


def extract_body_fat(session):
    pass


if __name__ == "__main__":
    file_data = parse()
    sessions = extract_sessions(file_data, 3)
