try:
    from bottle import route, run, request, abort, auth_basic
except:
    print("Please install the HTTP server dependencies: pip install 'wren-notes[http]'")
    exit(1)
from wren.core import (
    create_new_task,
    mark_task_done,
    get_tasks,
    get_task_content,
    config,
)
from json import dumps

back = "<br /><a href='/'>back</a>"
create_form = "<br /><form method='POST' action='/'><textarea name='task'></textarea><br/><button type='submit'>create new</button></form>"


def is_request_html(request):
    headers = request.headers
    return "html" in headers["Accept"]


def is_authenticated_user(user, password):
    if config["http_user"] == user and config["http_password"] == password:
        return True
    else:
        return False


def auth(func):
    if not config["http_user"] and not config["http_password"]:
        return func
    return auth_basic(is_authenticated_user)(func)


@route("/", method="GET")
@auth
def query():
    tasks = get_tasks()
    if is_request_html(request):
        return (
            "<script>const done = async(n) => { await fetch(`/${n}`, {method: 'DELETE'} ); location.reload() }</script><ul>"
            + "".join(
                [
                    f"<li><a href='/{item}'>{item}</a> <button onclick='done(\"{item}\")'>delete</button></li>"
                    for item in tasks
                ]
            )
            + "</ul>"
            + create_form
        )
    return {"tasks": get_tasks()}


@route("/", method="POST")
@auth
def create():
    filename = ""
    value = ""
    if request.json:
        value = request.json["task"]
    else:
        value = request.forms.get("task")
    if request.body:
        filename = create_new_task(value)
    if is_request_html(request):
        if filename:
            return f"<p>task created successfully: {filename}</p>" + back
        else:
            abort(400, "<p>couldn't create empty task</p>")
    if filename:
        return {"task": filename}
    else:
        abort(400, dumps({"error": "task is empty"}))


@route("/<task>", method="GET")
@auth
def read_content(task):
    content = get_task_content(task)
    if is_request_html(request):
        return "<pre>" + content + "</pre>" + back
    return {"content": content}


@route("/<task>", method="DELETE")
@auth
def done(task):
    response = mark_task_done(task)
    if is_request_html(request):
        return "<p>" + response + "</p>" + back
    return {"result": response}


def start_server():
    run(host="localhost", port=8080)
