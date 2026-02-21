import sqlite3
import re
import os

from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

DB = ":memory:"
TEMPLATE_STORAGE = "template_storage"

os.makedirs(TEMPLATE_STORAGE, exist_ok=True)

def filter_out_ok(columns):
    return [o for o in columns if not o.pk]

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def extract_table_name(sql):
    match = re.search(r"create table\s+(\w+)", sql, re.IGNORECASE)
    return match.group(1)


def introspect(sql):

    conn = get_conn()

    conn.executescript(sql)

    table = extract_table_name(sql)

    columns = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    conn.close()

    return table, columns


def map_type(sqlite_type):

    t = sqlite_type.upper()

    if "INT" in t:
        return "number"

    if "REAL" in t or "DECIMAL" in t or "FLOAT" in t:
        return "number"

    if "DATE" in t:
        return "date"

    return "text"


generator_env = Environment(
    loader=FileSystemLoader(TEMPLATE_STORAGE),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)


@app.route("/", methods=["GET", "POST"])
def index():

    generated = None
    templates = os.listdir(TEMPLATE_STORAGE)

    if request.method == "POST":

        sql = request.form["sql"]
        template_name = request.form["template"]

        table, columns = introspect(sql)

        template = generator_env.get_template(template_name)

        generated = template.render(
            table=table,
            columns=columns,
            #columns_no_pk=filter_out_ok(columns),
            map_type=map_type
        )

    return render_template(
        "index.html",
        generated=generated,
        templates=templates
    )


@app.route("/templates")
def templates_list():

    files = os.listdir(TEMPLATE_STORAGE)

    return render_template(
        "templates_list.html",
        files=files
    )


@app.route("/templates/new", methods=["GET", "POST"])
def new_template():

    if request.method == "POST":

        name = request.form["name"].strip()

        if not name.endswith(".jinja"):
            name += ".jinja"

        path = os.path.join(TEMPLATE_STORAGE, name)

        if os.path.exists(path):
            return "Template já existe", 400

        with open(path, "w") as f:
            f.write("""<h2>{{ table }}</h2>

{% for col in columns %}
{{ col.name }}
{% endfor %}
""")

        return redirect(url_for("edit_template", name=name))

    return render_template("template_new.html")


@app.route("/templates/edit/<name>", methods=["GET", "POST"])
def edit_template(name):

    path = os.path.join(TEMPLATE_STORAGE, name)

    if request.method == "POST":

        content = request.form["content"]

        with open(path, "w") as f:
            f.write(content)

        return redirect(url_for("templates_list"))

    with open(path) as f:
        content = f.read()

    return render_template(
        "template_edit.html",
        name=name,
        content=content
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
