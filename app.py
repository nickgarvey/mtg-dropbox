from flask import Flask

app = Flask(__name__)


@app.route("/")
async def root():
    return "hello"


# start scheduler to fetch json
# start scheduler to fetch dropbox
