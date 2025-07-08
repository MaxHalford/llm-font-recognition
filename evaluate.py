# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "rich"
# ]
# ///


import dataclasses
import functools
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
    instructions: str | None
    img_url: str
    identified_font: str | None


@dataclasses.dataclass
class Guess:
    task_id: str
    model_name: str
    candidate_font_1: str | None
    candidate_font_2: str | None
    candidate_font_3: str | None
    candidate_font_4: str | None
    candidate_font_5: str | None

    def as_list(self) -> list[str]:
        return [
            font
            for font in [
                self.candidate_font_1,
                self.candidate_font_2,
                self.candidate_font_3,
                self.candidate_font_4,
                self.candidate_font_5,
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
## Do LLMs recognise fonts?

This is a live benchmark of various LLMs' ability to recognise fonts from images.
The latter are scraped from [dafont.com](https://www.dafont.com/forum/?f=1). Each LLM is asked to
identify the font whenever a new image is uploaded by a user. The guesses are compared against the
actual font, once it has been identified by someone and confirmed. This process avoids benchmark
contamination.

The source code for this benchmark is available on [GitHub](https://github.com/MaxHalford/llm-font-recognition).

*Updated at {last_scraped_at}*

            """,
                justify="left",
            ),
            width=80,
        ),
    )

    console.print()

    # METRICS

    metrics = rich.table.Table(
        title="Metrics", title_justify="left", title_style="bold", header_style=""
    )
    metrics.add_column("Metric", justify="center", style="magenta", no_wrap=True)
    for model in models:
        metrics.add_column(model, justify="center", no_wrap=True)
    row = ["Total tasks"]
    for model in models:
        total_tasks = sum(
            1
            for task in complete_tasks
            if task.task_id in guesses_by_task
            and model in guesses_by_task[task.task_id]
        )
        row.append(f"{total_tasks:,d}")
    metrics.add_row(*row)
    ## TOP-K ACCURACY
    for k in range(1, 6):
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

    breakdown = rich.table.Table(
        title="Breakdown", title_justify="left", title_style="bold", header_style=""
    )
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
                font_to_show = next(
                    filter(
                        functools.partial(
                            check_if_guess_is_correct,
                            identified_font=task.identified_font,
                        ),
                        guessed_fonts,
                    ),
                    None,
                )
                index = guessed_fonts.index(font_to_show) if font_to_show else None
                cell.append(
                    f"{font_to_show} ({index + 1})"
                    if font_to_show
                    else guessed_fonts[0],
                    style=("green" if font_to_show else "red"),
                )
                row.append(cell)
            else:
                row.append("")

        breakdown.add_row(*row)

    console.print(breakdown)
    console.save_html("index.html")


if __name__ == "__main__":
    main()
