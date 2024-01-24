import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import json
from platformdirs import user_data_dir
from core import (
    create_new_task,
    get_summary,
    mark_task_done,
    get_tasks,
    get_task_content,
    config,
)

bot = telebot.TeleBot(config["telegramToken"])
scheduler = BackgroundScheduler()

data_dir = user_data_dir("knowts", "knowts")
schedules_path = os.path.join(data_dir, "schedules.json")


def get_all_schedules():
    try:
        with open(schedules_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


@bot.message_handler(commands=["list"])
def list_tasks(message):
    filter = " ".join(message.text.split(" ")[1:])
    tasks = get_tasks(filter)
    response = "".join(map(lambda t: "- " + t + "\n", tasks))
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=["summary"])
def summary(message):
    summary = get_summary()
    bot.send_message(message.chat.id, summary)


@bot.message_handler(commands=["done", "d", "do", "don"])
def mark_as_done(message):
    name = " ".join(message.text.split(" ")[1:])
    response = mark_task_done(name)
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=["read"])
def read_task(message):
    name = " ".join(message.text.split(" ")[1:])
    response = get_task_content(name)
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(
        message.chat.id,
        "knowts\n\n- enter any text to save it as task\n- mark a task as done by `/done foo`",
    )


@bot.message_handler(commands=["start"])
def start(message):
    bot.set_my_commands(
        [
            telebot.types.BotCommand(command="help", description="Help"),
            telebot.types.BotCommand(command="summary", description="Summary"),
            telebot.types.BotCommand(command="list", description="List"),
            telebot.types.BotCommand(command="schedule", description="Schedule"),
        ]
    )
    bot.set_chat_menu_button(
        message.chat.id, telebot.types.MenuButtonCommands("commands")
    )
    bot.send_message(message.chat.id, "knowts.\n\nuse /help to get help")


@bot.message_handler(commands=["schedule"])
def create_scheduled_message(message):
    schedule = " ".join(message.text.split(" ")[1:])
    job = [message.chat.id, schedule]

    # read current schedules
    schedules = get_all_schedules()

    if not schedule:
        my_schedules = [s[1] for s in schedules if s[0] == message.chat.id]
        if my_schedules:
            bot.send_message(
                message.chat.id,
                f'your summaries are scheduled for: {", ".join(my_schedules)}',
            )
        else:
            bot.send_message(message.chat.id, f"you got nothing scheduled!")
        return

    # save new schedule
    schedules.extend([job])
    with open(schedules_path, "w") as file:
        json.dump(schedules, file, indent=2)

    # register it
    scheduler.add_job(
        send_summary,
        CronTrigger.from_crontab(schedule),
        kwargs={"chat_id": message.chat.id},
    )
    bot.send_message(message.chat.id, f"Added a schedule: {schedule}")


@bot.message_handler(
    func=lambda message: len(message.text) > 3 and not message.text.startswith("/")
)
def add(message):
    filename = create_new_task(message.text)
    bot.send_message(message.chat.id, "added: " + filename)


@bot.message_handler(func=lambda message: True)
def reply_no(message):
    bot.reply_to(message, "not sure what you want. seek /help")


def send_summary(chat_id):
    bot.send_message(chat_id, get_summary())


schedules = get_all_schedules()
for schedule in schedules:
    scheduler.add_job(
        send_summary,
        CronTrigger.from_crontab(schedule[1]),
        kwargs={"chat_id": schedule[0]},
    )


def start_bot():
    print("Starting telegram bot")
    scheduler.start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
