# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "rich"
# ]
# ///


import dataclasses
import itertools
import json

import rich.console
import rich.markdown
import rich.table
import rich.text


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

    def as_list(self) -> list[str]:
        return [
            font
            for font in [
                self.candidate_font_1,
                self.candidate_font_2,
                self.candidate_font_3,
            ]
            if font
        ]


def check_if_guess_is_correct(guessed_font: str, identified_font: str) -> bool:
    return guessed_font.lower() == identified_font.lower()


def main():
    with open("tasks.json") as f:
        tasks = [Task(**task) for task in json.load(f)]
        complete_tasks = [
            task for task in reversed(tasks) if task.identified_font is not None
        ]

    with open("guesses.json", "r") as f:
        guesses = [Guess(**guess) for guess in json.load(f)]
        guesses_by_task = {
            task_id: {guess.model_name: guess for guess in guesses}
            for task_id, guesses in itertools.groupby(
                sorted(guesses, key=lambda g: g.task_id), key=lambda g: g.task_id
            )
        }
        models = sorted(set(guess.model_name for guess in guesses))

    with open("last_scraped_at.txt", "r") as f:
        last_scraped_at = f.read().strip()

    # DESCRIPTION
    console = rich.console.Console(record=True)
    console.print(
        rich.align.Align(
            rich.markdown.Markdown(
                f"""
## Can LLMs recognise fonts?

This is a live benchmark of various LLMs' ability to recognise fonts from images.
The latter are scraped from [dafont.com](https://www.dafont.com/forum/?f=1). Each LLM is asked to
identify the font used in newly uploaded images. The guesses are compared against the actual font
once it has been identified by a user. This process ensures there is no benchmark contamination.

The source code for this benchmark is available on [GitHub](https://github.com/MaxHalford/llm-font-recognition).

Last update made at {last_scraped_at}

            """,
                justify="left",
            ),
            width=80,
        ),
    )

    console.print()

    # METRICS

    metrics = rich.table.Table(title="Metrics", title_justify="left")
    metrics.add_column("Metric", justify="center", style="magenta", no_wrap=True)
    for model in models:
        metrics.add_column(model, justify="center", no_wrap=True)
    ## TOP-K ACCURACY
    for k in range(1, 4):
        row = [f"Top-{k} accuracy"]
        for model in models:
            correct_guesses = sum(
                any(
                    check_if_guess_is_correct(
                        guessed_font=guessed_font, identified_font=task.identified_font
                    )
                    for guessed_font in guesses_by_task[task.task_id][model].as_list()[
                        :k
                    ]
                )
                for task in complete_tasks
                if task.task_id in guesses_by_task
                and model in guesses_by_task[task.task_id]
            )
            total_guesses = sum(
                1
                for task in complete_tasks
                if task.task_id in guesses_by_task
                and model in guesses_by_task[task.task_id]
            )
            accuracy = correct_guesses / total_guesses if total_guesses > 0 else 0
            row.append(f"{accuracy:.2%}")
        metrics.add_row(*row)
    console.print(metrics)
    console.print()

    # BREAKDOWN

    breakdown = rich.table.Table(title="Breakdown", title_justify="left")
    breakdown.add_column("Task", justify="center", style="cyan", no_wrap=True)
    breakdown.add_column("Identified font", justify="center", no_wrap=True)
    for model in models:
        breakdown.add_column(model, justify="center", style="yellow", no_wrap=True)

    for task in complete_tasks:
        if task.task_id not in guesses_by_task:
            continue
        row = [f"[link={task.url}]{task.task_id}[/link]", task.identified_font]
        for model in sorted(models):
            if guess := guesses_by_task[task.task_id].get(model):
                cell = rich.text.Text()
                guessed_fonts = guess.as_list()
                for i, font in enumerate(guessed_fonts):
                    cell.append(
                        font,
                        style=(
                            "green"
                            if check_if_guess_is_correct(
                                guessed_font=font, identified_font=task.identified_font
                            )
                            else "red"
                        ),
                    )
                    if i < len(guessed_fonts) - 1:
                        cell.append(", ", style="dim")
                row.append(cell)
            else:
                row.append("")

        breakdown.add_row(*row)

    console.print(breakdown)
    console.save_html("index.html")


if __name__ == "__main__":
    main()
