from app.config.settings import Settings
from app.infrastructure.bootstrap import bootstrap_application


def main() -> None:
    settings = Settings()
    bootstrap_application(settings)


if __name__ == "__main__":
    main()
