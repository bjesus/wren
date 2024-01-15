import os
import shutil
from pathvalidate import sanitize_filename
import requests
import json
from datetime import datetime
from platformdirs import user_data_dir, user_config_dir

# import pprint
# pp = pprint.PrettyPrinter().pprint

notes_dir = os.path.expanduser("~/Notes")
done_dir = os.path.join(notes_dir, "done")
data_dir = user_data_dir("knowts", "knowts")
config_dir = user_config_dir("knowts", "knowts")
messages_log = os.path.join(data_dir, "messages.json")

config = {
    "mode": "single-user",
    "openaiToken": "",
    "telegramToken": "",
    "notes_dir": os.path.expanduser("~/Notes"),
}

try:
    with open(os.path.join(config_dir, "knowts.json"), "r") as file:
        user_config = json.load(file)
except FileNotFoundError:
    user_config = {}
config = {**config, **user_config}


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


mkdir(data_dir)
mkdir(notes_dir)
mkdir(done_dir)


def create_new_task(content):
    filename = sanitize_filename(content.split("\n")[0])
    content = "\n".join(content.split("\n")[1:])
    with open(os.path.join(notes_dir, filename), "w") as file:
        file.write(content)
    return filename


def get_tasks(s=""):
    files = [
        file
        for file in os.listdir(notes_dir)
        if os.path.isfile(os.path.join(notes_dir, file))
        and not file.startswith(".")
        and s in file
    ]
    return sorted(
        files, key=lambda x: os.path.getctime(os.path.join(notes_dir, x)), reverse=True
    )


def get_summary():
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
                "content": "You are a helpful assistant that helps the user be on top of the schedule and tasks. every once in a while, the user is going to send you the current time and a list of currently pending tasks. your role is to tell the user in a simple language what they need to do today. IF AND ONLY IF a task has been ongoing for a long time, let the user know about it. IF AND ONLY IF you see a task that appeared earlier in the chat but doesn't appear anymore, add a small congratulation to acknowledge the fact that the task was completed. the user will send each task in a new line starting with a dash. words starting with a plus sign are tags related to task. when writing back to the user, try to mention tasks that share the same tags or concept together and be concise.",
            },
        ]
        + existing_data
        + [current_message],
    }
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + config["openaiToken"],
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    response = data["choices"][0]["message"]["content"]

    existing_data.extend([current_message, data["choices"][0]["message"]])

    with open(messages_log, "w") as file:
        json.dump(existing_data, file, indent=2)

    return response


def get_task_file(name):
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


def mark_task_done(name):
    found, filename = get_task_file(name)
    if found:
        shutil.move(os.path.join(notes_dir, filename), os.path.join(done_dir, filename))
        response = f'marked "{filename}" as done'
    else:
        response = filename
    return response


def get_task_content(name):
    found, filename = get_task_file(name)
    if found:
        file_to_read = os.path.join(notes_dir, filename)
        with open(file_to_read, "r") as file:
            file_content = file.read()
            response = f"{filename}\n\n{file_content}"
    else:
        response = filename
    return response
