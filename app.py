from flask import Flask, redirect, render_template, request, url_for

from template_generator.core import (
    DEFAULT_TEMPLATE_CONTENT,
    generate_from_sql,
    list_template_names,
    read_template,
    write_template,
)


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    generated = None
    templates = list_template_names()
    sql = ""

    if request.method == "POST":
        sql = request.form["sql"]
        template_name = request.form["template"]
        _, generated = generate_from_sql(sql, template_name)

    return render_template(
        "index.html",
        generated=generated,
        templates=templates,
        sql=sql,
    )


@app.route("/templates")
def templates_list():
    return render_template(
        "templates_list.html",
        files=list_template_names(),
    )


@app.route("/templates/new", methods=["GET", "POST"])
def new_template():
    if request.method == "POST":
        try:
            name = write_template(
                request.form["name"],
                DEFAULT_TEMPLATE_CONTENT,
                overwrite=False,
            )
        except FileExistsError:
            return "Template ja existe", 400
        except ValueError as error:
            return str(error), 400

        return redirect(url_for("edit_template", name=name))

    return render_template("template_new.html")


@app.route("/templates/edit/<path:name>", methods=["GET", "POST"])
def edit_template(name):
    if request.method == "POST":
        try:
            write_template(name, request.form["content"])
        except ValueError as error:
            return str(error), 400

        return redirect(url_for("templates_list"))

    try:
        content = read_template(name)
    except ValueError as error:
        return str(error), 400

    return render_template(
        "template_edit.html",
        name=name,
        content=content,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
