# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4",
#     "requests",
# ]
# ///
import dataclasses
import datetime as dt
import json
import logging
import urllib.parse
import re
import typing

import bs4
import requests


@dataclasses.dataclass
class Task:
    task_id: str
    url: str
    title: str
    img_url: str
    identified_font: str | None


@dataclasses.dataclass
class TaskThumb:
    task_id: StopAsyncIteration
    url: str
    updated_at: dt.datetime


def parse_task_from_task_url(task_url: str, session: requests.Session) -> Task:
    response = session.get(task_url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    user_img = next(
        img
        for img in soup.find_all("img")
        if img.get("src", "").startswith("/forum/attach/orig")
    )
    user_img_url = urllib.parse.urljoin("https://www.dafont.com", user_img["src"])
    user_img_alt = user_img.get("alt", "")
    identified_font = next(
        (
            div.find("a").text
            for div in soup.find_all("div")
            if div.text.startswith("Identified font:") and div.find("a")
        ),
        None,
    )
    return Task(
        task_id=urllib.parse.urlsplit(task_url).path.split("/")[3],
        url=task_url,
        title=user_img_alt,
        img_url=user_img_url,
        identified_font=identified_font,
    )


def _loop_task_thumbs(
    page_no: int, session: requests.Session
) -> typing.Generator[TaskThumb, None, None]:
    url = f"https://www.dafont.com/forum/?f=1&p={page_no}"
    response = session.get(url)
    response.raise_for_status()

    update_pattern = (
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} at \d{2}:\d{2}\b"
    )
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    for thumb in soup.find_all("div", class_="thumb_cont"):
        path = thumb.find("div", class_="thumb_img").find("a").get("href")
        url = urllib.parse.urljoin("https://www.dafont.com/forum/", path)
        at_str = re.search(
            update_pattern, thumb.find("div", class_="nobr dfsmall tdh").text
        )
        year = dt.datetime.now().year
        at_dt = dt.datetime.strptime(f"{year} {at_str.group()}", "%Y %b %d at %H:%M")
        yield TaskThumb(task_id=path.split("/")[1], url=url, updated_at=at_dt)


def loop_task_thumbs(
    session: requests.Session,
) -> typing.Generator[TaskThumb, None, None]:
    page_no = 1
    while True:
        logging.info(f"Checking page {page_no}")
        yield from _loop_task_thumbs(page_no, session)
        page_no += 1


def save_tasks(tasks: dict[int, Task], filename: str = "tasks.json") -> None:
    with open(filename, "w") as f:
        json.dump(
            [dataclasses.asdict(task) for task_id, task in tasks.items()], f, indent=4
        )
        logging.info(f"Saved tasks to {filename}")


def main():
    session = requests.Session()
    # Define a realistic browser headers dictionary
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }
    )

    with open("tasks.json") as f:
        tasks = {task["task_id"]: Task(**task) for task in json.load(f)}

    with open("last_scraped_at.txt") as f:
        last_scraped_at = dt.datetime.fromisoformat(f.read().strip())
    new_last_scraped_at = last_scraped_at

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    for i, task_thumb in enumerate(loop_task_thumbs(session)):
        if task_thumb.updated_at < last_scraped_at:
            break
        new_last_scraped_at = max(new_last_scraped_at, task_thumb.updated_at)

        if task_thumb.task_id in tasks:
            continue

        task = parse_task_from_task_url(task_url=task_thumb.url, session=session)
        tasks[task.task_id] = task

        logging.info(f"Added task {task.task_id} ~ {task.url}")

        if i % 10 == 0:
            save_tasks(tasks)

    save_tasks(tasks)

    with open("last_scraped_at.txt", "w") as f:
        f.write(new_last_scraped_at.isoformat())


if __name__ == "__main__":
    main()
