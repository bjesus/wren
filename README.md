<h1 align="center">
Wren
</h1>

<p align="center">
a note taking application and a to-do management system that is ridiculously simple, yet very advanced.
</p>
<p align="center">
<img src="https://github.com/bjesus/knowts/assets/55081/ab1f5584-267c-45da-b7bd-96fb38c66143" height="200">
</p>

It is simple because every note is just a file. The filename is the title, and the content is the note's content. Forget about HTML, Markdown - we're talking plain text. Just write. If you want a task to repeat every Saturday you just prefix it with a cron syntax, e.g. `0 8 * * 6 weekly swim`, and if you want a task to appear from a specific time you just start it with the date, like `2030-01-01 check if Wren became super popular`.

It is advanced because it is very extensible - it comes (optionally!) with a Telegram bot that you can chat with to manage your notes, and even get AI-driven daily summaries. It also includes a tiny HTTP server that you can use to manage tasks using an API or from the browser.

## Usage

The management of tasks in Wren is simple:
- Tasks are just files living your `notes` folder. You might as well create them with `touch task` and edit them with `vim task`
- Completed tasks are moved to your `done` folder.
- Tasks starting with a timestamp will not appear in the list before their time
- Tasks starting with a cron signature will not be moved when completed. Instead they'll be copied to the `done` directory, and will reappear automatically when the the copied file is old enough.

### Basic usage

The regular usage mode Wren is the command line. For the following examples, `n` is my alias to `wren`, but you can use any alias or just call `wren` directly. Normal tasks can be created by just typing them
```
$ n my new task
created task: my new task

$ n my other note
created task: my other note

$ n 'task with some content
anything you put from here on will
go inside the file content
created task: task with some content
```

Reading a task content is done with the `-r` flag:
```
$ n -r some
task with some content
anything you put from here on wiil
go inside the file content
```
Note that when referring to a task, you can give Wren any part of the task title.

Listing your current tasks is done with `n`, or if you want to filter you can use `n -l query`:
```
$ n
➜ task with some content
➜ my other note
➜ my new task

$ n -l my
➜ my other note
➜ my new task
```

Use  `-e` to edit a task in your `$EDITOR` or `-d` to mark it as done:
```
$ n -d some
marked "task with some content" as done
```

### Integrations

##### Random task
Use `--one` to print one random task. When would you ever use that? I'm using it with Waybar to always have one task displayed at the bottom of my screen, like this:
```
  "custom/task": {
    "tooltip": true,
    "max-length": 20,
    "interval": 60,
    "exec": "wren --one"
  },
```

##### AI Assistant

Wren can also work like an AI Assistant. If you use `--summary` it will use GPT4 to create a nice human like message telling you what's waiting for you today, and congratulates you for the stuff you have completed recently. You can use it to update `/etc/motd` daily, or through the Telegram bot (below).

##### Telegram bot

Using `--telegram` will spin up a Telegram bot listener that will respond to your messages and allow you to create tasks, list them, edit them and so on. It will also allow you to set a cron-based schedule for receiving AI Assistant messages. This can be handy if you want to start your day with a message from Wren telling you about your upcoming tasks.

- List tasks using `/list`
- Create task by just writing it, e.g. `my new task`
- Mark as done with `/done task`
- See more at `/help`

If you want to run it outside your computer (e.g. so it's always available), I highly recommend using [Syncthing](https://syncthing.net/) to sync your notes.

##### HTTP Server

With `--http` you get both a simple tiny website that works through the browser, and an API server that accepts and returns JSON. Either browse to `http://localhost:8080` or send requests directly with the proper headers:
- List tasks: `curl http://localhost:8080`
- Create task: `curl http://localhost:8080 -d '{"task": "create HTTP interface"}' -H 'content-type: application/json'`
- Mark as done: `curl http://localhost:8080/content -X DELETE`

The HTTP server can be used to integrate with voice assistants, [Home Assistant](https://www.home-assistant.io/), [Tasker](https://joaoapps.com/tasker/) etc. Like with the Telegram bot, if you want to run it outside your computer, I highly recommend using [Syncthing](https://syncthing.net/).

## Configuration

See the configuration path for your OS using `--help`.

The schema is as follows and all keys are optional. Remove the comments from your actual file.
```
{
  "notes_dir": "~/Notes",  // This can absolute or include ~
  "done_dir": "done",      // This can be relative to the notes dir, or absolute
  "openai_token": "",      // Fill this if you want to use summaries
  "telegram_token": "",    // Fill this if you want the Telegram bot
  "allowed_telegram_chats": [
    1234564868             // Initiating a chat will print out the chat ID you should fill here
  ],
  // Below you can put context to give the AI assistant
  "about_user": "I work at NASA as Product Manager. Mars is the name of my dog." 
}
```
