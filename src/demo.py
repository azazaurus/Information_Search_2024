from flask import Flask, render_template, request
from urllib.parse import unquote_plus

app = Flask(__name__, static_folder = "../static", template_folder = "../templates")


@app.route("/")
def search():
    decoded_query = unquote_plus(bytes.decode(request.query_string, errors = "replace"))
    search_query = decoded_query[len("query="):]
    search_results = []
    return render_template("search.html", search_query = search_query, search_results = search_results)


if __name__ == "__main__":
    app.run()
