#!/usr/bin/env python3

import os
import argparse
import subprocess
from random import choice
from wren.core import (
    create_new_task,
    get_summary,
    get_task_content,
    get_task_file,
    get_tasks,
    mark_task_done,
    notes_dir,
    config_file,
    data_dir,
    __version__,
)

editor = os.environ.get("EDITOR", "vi")


def create_file(name):
    filename = create_new_task(name)
    print("created task:", filename)


def list_files(s=""):
    tasks = get_tasks(s)
    print("".join(map(lambda t: "➜ " + t + "\n", tasks))[:-1])


def print_random():
    tasks = get_tasks("")
    print(choice(tasks))


def print_summary():
    summary = get_summary()
    print(summary)


def edit_content(name):
    found, filename = get_task_file(name)
    if found:
        filepath = os.path.join(notes_dir, filename)
        subprocess.run([editor, filepath])


def read_content(name):
    content = get_task_content(name)
    print(content)


def mark_done(name):
    message = mark_task_done(name)
    print(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", nargs="*", help="a new task to be created")
    parser.add_argument(
        "-l",
        "--ls",
        "--list",
        type=str,
        help="List all current tasks",
        nargs="?",
        const="",
        default=None,
    )
    parser.add_argument(
        "-d", "--done", metavar="foo", type=str, help="Mark a task as done"
    )
    parser.add_argument(
        "-r", "--read", metavar="foo", type=str, help="Read a task content"
    )
    parser.add_argument(
        "-e", "--edit", metavar="foo", type=str, help="Edit a task content"
    )
    parser.add_argument(
        "-o", "--one", action="store_true", help="Print one random task"
    )
    parser.add_argument(
        "-s", "--summary", action="store_true", help="Generate a summary"
    )
    parser.add_argument("--telegram", action="store_true", help="Start Telegram bot")
    parser.add_argument("--http", action="store_true", help="Start HTTP server")
    parser.add_argument("--version", action="store_true", help="Show Wren version")

    args = parser.parse_args()

    if args.ls != None:
        list_files(args.ls)
    elif args.version:
        print("Wren " + __version__)
        print("\nconfig: " + config_file)
        print("data directory: " + data_dir)
    elif args.http:
        from wren.http_server import start_server

        start_server()
    elif args.telegram:
        from wren.telegram import start_bot

        start_bot()
    elif args.one:
        print_random()
    elif args.edit:
        edit_content(args.edit)
    elif args.summary:
        print_summary()
    elif args.read:
        read_content(args.read)
    elif args.done:
        mark_done(args.done)
    else:
        if args.task:
            create_file(" ".join(args.task))
        else:
            list_files()


if __name__ == "__main__":
    main()
