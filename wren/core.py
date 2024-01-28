import os
import shutil
from pathvalidate import sanitize_filename
import requests
import json
from datetime import datetime
from dateutil import parser
from platformdirs import user_data_dir, user_config_dir
from croniter import croniter

__version__ = "0.1.2"

# Load config and set up folders

data_dir = user_data_dir("wren", "wren")
config_dir = user_config_dir("wren", "wren")
messages_log = os.path.join(data_dir, "messages.json")

config = {
    "notes_dir": "~/Notes",
    "done_dir": "~/Notes/done",
    "openai_token": "",
    "telegram_token": "",
    "allowed_telegram_chats": [],
    "about_user": "The user chose to specify nothing.",
}

config_file = os.path.join(config_dir, "wren.json")

try:
    with open(config_file, "r") as file:
        user_config = json.load(file)
except FileNotFoundError:
    user_config = {}
config = {**config, **user_config}


def parse_path(p, base=""):
    return os.path.join(base, os.path.expanduser(p))


notes_dir = parse_path(config["notes_dir"])
done_dir = parse_path(config["done_dir"], notes_dir)

now = datetime.now()


def mkdir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


mkdir(data_dir)
mkdir(notes_dir)
mkdir(done_dir)


# Common API


def create_new_task(content: str) -> str:
    filename = sanitize_filename(content.split("\n")[0].replace("*", "＊"))
    content = "\n".join(content.split("\n")[1:])
    with open(os.path.join(notes_dir, filename), "w") as file:
        file.write(content)
    return filename


def get_tasks(query="") -> list[str]:
    global now
    now = datetime.now()
    return [
        format_task_name(file)
        for file in sorted(
            os.listdir(notes_dir),
            key=lambda x: os.path.getctime(os.path.join(notes_dir, x)),
            reverse=True,
        )
        if os.path.isfile(os.path.join(notes_dir, file))
        and not file.startswith(".")
        and query in file
        and is_present_task(file)
    ]


def get_summary() -> str:
    url = "https://api.openai.com/v1/chat/completions"
    current_time = datetime.now().isoformat()
    tasks = get_tasks()
    current_message = {"role": "user", "content": f"{current_time}\n{tasks}"}

    try:
        with open(messages_log, "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that helps the user be on top of their schedule and tasks. every once in a while, the user is going to send you the current time and a list of currently pending tasks. your role is to tell the user in a simple language what they need to do today. IF AND ONLY IF a task has been ongoing for a long time, let the user know about it. IF AND ONLY IF you see a task that appeared earlier in the chat but doesn't appear anymore, add a small congratulation to acknowledge the fact that the task was completed. the user will send each task in a new line starting with a dash. words starting with a plus sign are tags related to task. when writing back to the user, try to mention tasks that share the same tags or concept together and be concise. The user added the following context: "
                + config["about_user"],
            },
        ]
        + existing_data
        + [current_message],
    }
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + config["openai_token"],
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    response = data["choices"][0]["message"]["content"]

    existing_data.extend([current_message, data["choices"][0]["message"]])

    with open(messages_log, "w") as file:
        json.dump(existing_data, file, indent=2)

    return response


def get_task_file(name: str) -> tuple[bool, str]:
    matching_files = [
        file
        for file in os.listdir(notes_dir)
        if name.lower() in file.lower()
        and os.path.isfile(os.path.join(notes_dir, file))
    ]
    if len(matching_files) == 1:
        return (True, matching_files[0])
    elif len(matching_files) > 1:
        return (False, "Error: Multiple matching files found.")
    else:
        return (False, f"Error: No matching file for '{name}' found.")


def mark_task_done(name: str) -> str:
    found, filename = get_task_file(name)
    if found:
        if is_cron_task(filename):
            shutil.copy(
                os.path.join(notes_dir, filename), os.path.join(done_dir, filename)
            )
        else:
            shutil.move(
                os.path.join(notes_dir, filename), os.path.join(done_dir, filename)
            )
        response = f'marked "{filename}" as done'
    else:
        response = filename
    return response


def get_task_content(name: str) -> str:
    found, filename = get_task_file(name)
    if found:
        file_to_read = os.path.join(notes_dir, filename)
        with open(file_to_read, "r") as file:
            file_content = file.read()
            response = f"{filename}\n\n{file_content}"
    else:
        response = filename
    return response


# Helper functions


def is_present_task(file: str) -> bool:
    if not file[0].isdigit():
        return True
    if is_cron_task(file):
        cron = " ".join(file.replace("＊", "*").split(" ")[:5])
        last_task = None
        path = os.path.join(done_dir, file)
        if os.path.exists(path):
            last_modified_date = datetime.fromtimestamp(os.path.getmtime(path))
            if last_task is None or last_modified_date > last_task:
                last_task = last_modified_date
            if not last_task or croniter(cron, last_task).get_next(datetime) <= now:
                return True
        else:
            return True
    elif is_dated_task(file):
        time = file.split(" ")[0]
        task_time = parser.parse(time)
        if task_time <= now:
            return True
    return False


def format_task_name(filename: str) -> str:
    if is_cron_task(filename):
        return " ".join(filename.split()[5:])
    if is_dated_task(filename):
        return " ".join(filename.split()[1:])
    return filename


def is_dated_task(filename: str) -> bool:
    try:
        parser.parse(filename.split()[0])
        return True
    except:
        return False


def is_cron_task(filename: str) -> bool:
    splitted = filename.split()
    if len(splitted) < 6 or not all(
        (s.isdigit() or s in ["＊", "*"]) for s in splitted[:3]
    ):
        return False
    return True
