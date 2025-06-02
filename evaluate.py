# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///


import dataclasses
import json


@dataclasses.dataclass
class Task:
    task_id: str
    url: str
    title: str
    img_url: str
    identified_font: str | None


@dataclasses.dataclass
class Guess:
    task_id: str
    model_name: str
    candidate_font_1: str | None
    candidate_font_2: str | None
    candidate_font_3: str | None


def main():
    with open("tasks.json") as f:
        tasks = [Task(**task) for task in json.load(f)]
        complete_tasks = {
            task.task_id: task for task in tasks if task.identified_font is None
        }

    with open("guesses.json", "r") as f:
        guesses = [Guess(**guess) for guess in json.load(f)]
        guesses_for_complete_tasks = {
            (guess.task_id, guess.model_name): guess
            for guess in guesses
            if guess.task_id in complete_tasks
        }

    print(len(guesses_for_complete_tasks))


if __name__ == "__main__":
    main()
