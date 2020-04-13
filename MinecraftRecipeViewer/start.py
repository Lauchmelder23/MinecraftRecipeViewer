from app import *

if __name__ == '__main__':
    with open("config.json") as file:
        data = json.loads(file.read())
        HOST = data["host"]
        PORT = data["port"]

        SSL_CERT_PATH = data.get("ssl_cert_path")
        SSL_PKEY_PATH = data.get("ssl_pkey_path")

        app.secret_key = "whocarestbh"

    if SSL_CERT_PATH == None or SSL_PKEY_PATH == None:
        app.run(HOST, PORT)
    else:
        app.run(HOST, PORT, ssl_context=(SSL_CERT_PATH, SSL_PKEY_PATH))