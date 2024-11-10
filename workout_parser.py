import os
import sys
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot
import matplotlib.dates as mdates


@dataclass
class Session:
    date: str
    unprocessed_lines: list
    weight: float = np.nan
    body_fat: float = np.nan
    exercises: list = field(default_factory=list)


@dataclass
class ExerciseVariation:
    grip_type: str  # e.g., 'ring', 'bar', 'parallettes'
    position_type: str  # e.g., 'knee', 'incline', 'decline'
    movement_type: str  # e.g., 'eccentric', 'isometric'


@dataclass
class Set:
    variation: ExerciseVariation
    reps: int
    alt_reps: int
    form: str
    rest_time: int


@dataclass
class Exercise:
    exercise_type: str
    sets: list[Set]


def parse():
    with open(Path(os.getcwd()) / "workouts.txt", "r", encoding="utf-8") as file:
        return file.read()


def split_lines(data, multiplier):
    newline = "\n"
    return data.split(multiplier * newline)


def extract_session_dates(sessions_text, file_bytes):
    session_dates = [i[:8] for i in sessions_text]

    assert set(session_dates) == set(list_session_dates(file_bytes))

    diff = [item for item in session_dates if session_dates.count(item) > 1]
    assert len(diff) == 0, f"Duplicate session dates found: {set(diff)}"

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
    for _, line in enumerate(split_unprocessed_lines):
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


def extract_variation(text):
    variation_regex = r"\(([^,]*),([^,]*),([^)]*)\)"
    variation = None
    try:
        # Check for a parenthesis before the colon
        if "(" in text and ")" in text:
            variation_match = re.search(variation_regex, text)
            # Assert that there are exactly two commas within the parenthesis
            assert (
                variation_match
            ), "Variation format error: expected two commas within parenthesis."

            # Extract the variation details within parentheses
            if variation_match:
                grip_type, position_type, movement_type = [
                    item.strip() for item in variation_match.groups()
                ]
                # Create ExerciseVariation object, handling missing data
                variation = ExerciseVariation(
                    grip_type or None,
                    position_type or None,
                    movement_type or None,
                )

    except AssertionError as e:
        print(f"Assertion Error on text '{text}': {e}")
        sys.exit(1)

    return variation


def extract_exercises(session):
    if session.unprocessed_lines != "":
        exercises_text_list = split_lines(session.unprocessed_lines, 2)
        session_exercises = []
        for sets_list in exercises_text_list:
            sets_list = split_lines(sets_list, 1)
            exercise_types = []
            sets = []
            for set_text in sets_list:
                # Find the position of the colon
                colon_position = set_text.find(":")

                # Extract the part of the string before the colon
                pre_colon_text = (
                    set_text[:colon_position] if colon_position != -1 else set_text
                )

                variation = extract_variation(pre_colon_text)

                # Extract the exercise type
                exercise_type_match = re.search(
                    r"(?<=- )(.*?)(?=\s*\(|[:,\n])", set_text
                )
                if exercise_type_match:
                    exercise_type = exercise_type_match.group(0).strip()

                    # Process the rest of the line
                    line = set_text[len(exercise_type) + 2 :]

                    pattern = r"(\d+)\s*([\w\s]+?)(?:\s*\(?(?:\s*(\d+)\s*OB)?\)?,)?\s*(?:(\d+)\s*min)?"
                    details_match = re.search(pattern, line)
                    if details_match:
                        reps, form, alt_reps, rest_time = details_match.groups()
                        reps = int(reps)
                        form = form.strip() if form else ""
                        alt_reps = int(alt_reps) if alt_reps else 0
                        rest_time = int(rest_time) if rest_time else 0

                        sets.append(Set(variation, reps, alt_reps, form, rest_time))

                    exercise_types.append(exercise_type)

            if len(exercise_types) > 0:
                exercise_types_set = set(exercise_types)
                if len(exercise_types_set) > 1:
                    print(exercise_types_set)
                assert (
                    len(exercise_types_set) == 1
                ), "Multiple exercise types found in a single set list"
                exercise_type = next(iter(exercise_types_set))

                session_exercises.append(Exercise(exercise_type, sets))
        session.exercises = session_exercises
        return session_exercises


def extract_body_fat(session):
    split_unprocessed_lines = session.unprocessed_lines.split("\n\n", 1)
    for _, line in enumerate(split_unprocessed_lines):
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


def print_session(session):
    print(
        f"\nSession date: {session.date}, weight: {session.weight}, body fat: {session.body_fat}"
    )
    if session.exercises:
        for e in session.exercises:
            print(f"  exercise: {e.exercise_type}, sets: {len(e.sets)}")
            for s in e.sets:
                variation_attributes = []
                if s.variation:
                    if s.variation.grip_type:
                        variation_attributes.append(
                            f"grip type: {s.variation.grip_type}"
                        )
                    if s.variation.position_type:
                        variation_attributes.append(
                            f"position type: {s.variation.position_type}"
                        )
                    if s.variation.movement_type:
                        variation_attributes.append(
                            f"movement type: {s.variation.movement_type}"
                        )
                var_str = ""
                if len(variation_attributes) > 0:
                    var_str = ", ".join(variation_attributes) + ", "
                print(
                    f"    {var_str}reps: {s.reps}, alt. reps: {s.alt_reps}, form: {s.form}, rest time: {s.rest_time}"
                )


def main():
    file_data = parse()
    # Three newline separators to separate sessions
    session_text_list = split_lines(file_data, 3)
    dates, sessions = extract_session_dates(session_text_list, file_data)
    weights = []
    for s in sessions:
        weights.append(extract_weight(s))
        extract_body_fat(s)
        extract_exercises(s)
        print_session(s)
    plot(dates, weights, "Weight", "kg")
    # plot(dates, body_fats, "Body Fat", "%")


if __name__ == "__main__":
    main()
