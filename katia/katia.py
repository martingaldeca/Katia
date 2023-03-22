import os
from ast import literal_eval

from katia.interpreter import KatiaInterpreter
from katia.owner import Owner
from katia.recognizer import KatiaRecognizer
from katia.speaker import KatiaSpeaker


class Katia:
    """
    Main class of the project. This will be the manager for the recognizer the
    interpreter and the speaker. When it is instanced it will start the different threads.
    """

    def __init__(self, owner: Owner, start: bool = True):
        self.name = os.getenv("KATIA_MAIN_NAME", "Katia")
        self.adjectives = literal_eval(os.getenv("KATIA_ADJECTIVES", "[]"))
        self.valid_names = literal_eval(os.getenv("KATIA_VALID_NAMES", "[]"))
        self.recognizer = KatiaRecognizer(
            valid_names=self.valid_names, owner_uuid=owner.uuid
        )
        self.interpreter = KatiaInterpreter(
            name=self.name, adjectives=self.adjectives, owner_uuid=owner.uuid
        )
        self.speaker = KatiaSpeaker(owner_uuid=owner.uuid)

        if start:
            self.start_katia()

    def start_katia(self):
        """
        Function to start Katia program. It will start the threads for the recognizer, the
        interpreter and the speaker.
        :return:
        """
        self.recognizer.start()
        self.interpreter.start()
        self.speaker.start()
