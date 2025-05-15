from app import create_app
from app.seed import run_seeds

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_seeds()
