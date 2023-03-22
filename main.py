from dotenv import load_dotenv

from katia.katia import Katia
from katia.logger_manager.logger import setup_logger
from katia.owner import Owner

if __name__ == "__main__":
    load_dotenv()
    setup_logger()

    owner = Owner(name="Katia User")
    Katia(owner=owner)
