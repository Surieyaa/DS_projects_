import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "pulsefit-dev-secret-change-in-production")

    # Defaults to local SQLite so the app runs with zero setup.
    # To use MySQL instead (as in the original spec), set an env var, e.g.:
    #   set DATABASE_URL=mysql+pymysql://user:password@localhost/pulsefit
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "pulsefit.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    EXERCISES_JSON = os.path.join(BASE_DIR, "data", "exercises.json")
    MEALS_JSON = os.path.join(BASE_DIR, "data", "meals.json")

    REPORTS_DIR = os.path.join(BASE_DIR, "static", "reports")
