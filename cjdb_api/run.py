from cjdb_api.app import make_app

def main():
    app = make_app()
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()

