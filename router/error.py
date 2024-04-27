from server import app


@app.errorhandler(500)
def handle_error():
    print("========================")
