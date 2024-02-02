try:
    import simplematrixbotlib as botlib
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except:
    print(
        "Please install the Telegram bot dependencies: pip install 'wren-notes[http]'"
    )
    exit(1)
import os
import json
from croniter import croniter
from platformdirs import user_data_dir
from wren.core import (
    create_new_task,
    get_summary,
    mark_task_done,
    get_tasks,
    get_task_content,
    config,
)

creds = botlib.Creds(config["homeserver"], config["matrix_localpart"], config["matrix_password"])
bot = botlib.Bot(creds)
PREFIX = '!'
COMMANDS = ["list", "summary", "done", "done", "do", "d", "read", "help", "schedule"]
scheduler = BackgroundScheduler()

data_dir = user_data_dir("wren", "wren")
schedules_path = os.path.join(data_dir, "schedules.json")

def get_all_schedules():
    try:
        with open(schedules_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

### list ###
@bot.listener.on_message_event
async def list_tasks(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    body = message.body
    filter = " ".join(body.split(" ")[1:])
    tasks = get_tasks(filter)
    if len(tasks) > 0:
        response = "".join(map(lambda t: "- " + t + "\n", tasks))
    else:
        response = "no current tasks\nenter any text to save it as task"
    if match.prefix() and match.command("list") and match.is_not_from_this_bot():
        await bot.api.send_text_message(
            room.room_id,
            response
        )

### summary ###
@bot.listener.on_message_event
async def summary(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    summary = get_summary()
    if match.prefix() and match.command("summary"):
        await bot.api.send_text_message(
            room.room_id,
            summary
        )

### done ###
@bot.listener.on_message_event
async def mark_as_done(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    if match.prefix() and match.command("done") or match.command("don") or match.command("do") or match.command("d") and match.is_not_from_this_bot():
        text = message.body
        name = " ".join(text.split(" ")[1:])
        response = mark_task_done(name)
        await bot.api.send_text_message(
            room.room_id,
            response
        )

### read ###
@bot.listener.on_message_event
async def read_task(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    if match.prefix() and match.command("read") and match.is_not_from_this_bot():
        text = message.body
        name = " ".join(text.split(" ")[1:])
        response = get_task_content(name)
        await bot.api.send_text_message(
            room.room_id,
            response
        )

### help ###
@bot.listener.on_message_event
async def help(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    if match.prefix() and match.command("help") and match.is_not_from_this_bot():
        await bot.api.send_text_message(
            room.room_id,
            "wren\n\n- enter any text to save it as task\n- mark a task as done by `/done foo`"
        )

### schedule ###
@bot.listener.on_message_event
async def create_scheduled_message(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    
    if match.prefix() and match.command("schedule") and match.is_not_from_this_bot():
        text = message.body
        schedule = " ".join(text.split(" ")[1:])
        job = [room.room_id, schedule]

        # read current schedules
        schedules = get_all_schedules()
        if not schedule:
            my_schedules = [s[1] for s in schedules if s[0] == room.room_id]
            if my_schedules:
                await bot.api.send_text_message(
                    room.room_id,
                    f'your summaries are scheduled for: {", ".join(my_schedules)}'
                )
            else:
                await bot.api.send_text_message(
                    room.room_id,
                    f"you got nothing scheduled!"
                )
            return

        # save new schedule
        schedules.extend([job])
        with open(schedules_path, "w") as file:
            json.dump(schedules, file, indent=2)

        # check if cron and register schedule
        if len(schedule) > 0:
            if schedule[0].isdigit() or schedule[0] in ['*', ',', '-', '/']:
                if schedule[1].isspace() and schedule[2].isdigit() or schedule[2] in ['*', ',', '-', '/']:
                    trigger = schedule[0:9]
                elif schedule[1].isdigit() or schedule[1] in ['*', ',', '-', '/']:
                    trigger = " ".join(s for s in schedule[0:5])
                # register it
                scheduler.add_job(
                    send_summary,
                    CronTrigger.from_crontab(trigger),
                    kwargs={"room": room.room_id},
                )
                await bot.api.send_text_message(
                    room.room_id,
                    f"Added a schedule: {schedule}"
                )   
            else:
                await bot.api.send_text_message(
                    room.room_id,
                    f"Please format as cron"
                )

### add ###
@bot.listener.on_message_event
async def add(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    if not match.prefix() and match.is_not_from_this_bot():
        text = message.body
        filename = create_new_task(text)
        await bot.api.send_text_message(
            room.room_id,
            "added: " + filename
        )

### reply no ###
@bot.listener.on_message_event
async def reply_no(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)
    command = message.body.split()[0]
    if match.prefix() and match.is_not_from_this_bot() and command[1:] not in COMMANDS:
        await bot.api.send_text_message(
            room.room_id,
            "not sure what you want. seek !help" + " entered: " + message.body
        )

### send summary ###
async def send_summary(room):
    await bot.api.send_text_message(
        room.room_id,
        get_summary()
    )

### start ###
def start_bot():
    print("Starting matrix bot")
    scheduler.start()
    bot.run()
