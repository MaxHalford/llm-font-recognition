# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "dotenv",
#     "llm",
#     "llm-anthropic",
#     "llm-gemini",
#     "llm-mistral",
#     "pydantic"
# ]
# ///

import dataclasses
import json
import logging
import textwrap
import time

import dotenv
import llm
import pydantic


# Load environment variables from .env file
dotenv.load_dotenv()


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


class FontClassificationSchema(pydantic.BaseModel):
    candidate_font_1: str | None
    candidate_font_2: str | None
    candidate_font_3: str | None
    candidate_font_4: str | None
    candidate_font_5: str | None


def make_guess(task: Task, model_name: str) -> Guess:
    model = llm.get_model(model_name)

    prompt = f"""

        You are an expert at identifying fonts. You are provided an image, and your goal is to
        identify the font used in the image. This images comes dafont.com, where users post
        images of fonts they are trying to identify. The image is attached to this prompt.

        Some images may contain multiple fonts. In that case you should leverage the additional
        context provided by the user to identify the most relevant font.

        You are allowed to make up to five guesses. You can leave the guesses blank if you are
        unsure.

        The title the user chose when posting the image is {task.title!r}.

        """
    if task.instructions:
        prompt += f"\nAdditional instructions provided by the user: {task.instructions}"
    prompt = textwrap.dedent(prompt).strip()

    response = model.prompt(
        prompt,
        schema=FontClassificationSchema,
        attachments=[llm.Attachment(url=task.img_url)],
    )

    output = json.loads(response.text())

    return Guess(
        task_id=task.task_id,
        model_name=model_name,
        candidate_font_1=output.get("candidate_font_1"),
        candidate_font_2=output.get("candidate_font_2"),
        candidate_font_3=output.get("candidate_font_3"),
        candidate_font_4=output.get("candidate_font_4"),
        candidate_font_5=output.get("candidate_font_5"),
    )


def save_guesses(
    guesses: dict[tuple[str, str], Guess], filename: str = "guesses.json"
) -> None:
    with open(filename, "w") as f:
        json.dump(
            [dataclasses.asdict(guess) for guess in guesses.values()], f, indent=4
        )
        logging.info(f"Saved tasks to {filename}")


def main():
    models = [
        "gpt-4o-mini",
        "gemini-2.5-flash-preview-05-20",
        # "claude-3.5-sonnet",
        # "mistral-large",  # doesn't support attachments
    ]

    with open("guesses.json", "r") as f:
        guesses = {
            (guess["task_id"], guess["model_name"]): Guess(**guess)
            for guess in json.load(f)
        }

    with open("tasks.json") as f:
        tasks = [Task(**task) for task in json.load(f)]
        incomplete_tasks = [task for task in tasks if task.identified_font is None]

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    for task in incomplete_tasks:
        any_guess_made = False
        for model_name in models:
            if (task.task_id, model_name) in guesses:
                continue

            try:
                guess = make_guess(task, model_name)
                guesses[(task.task_id, model_name)] = guess
                logging.info(
                    f"Made guess for {task.task_id} with {model_name}: {', '.join(guess.as_list())}"
                )
            except Exception as e:
                logging.error(f"Error processing {task.task_id} with {model_name}: {e}")
            any_guess_made = True

        if any_guess_made:
            # LLMs are expensive, so let's save often to avoid losing progress
            save_guesses(guesses)

            # To avoid hitting rate limits, we sleep for a bit after each request
            logging.info("Sleeping to avoid rate limits...")
            time.sleep(3)


if __name__ == "__main__":
    main()
