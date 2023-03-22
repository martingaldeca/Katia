import logging
import os
import re
from ast import literal_eval
from threading import Thread

import speech_recognition as sr
from pygame import mixer

from katia.message_manager import KatiaProducer

logger = logging.getLogger("KatiaRecognizer")


class KatiaRecognizer(Thread):
    """
    This is the main recognizer. It will run in a separate thread, and it will
    continuously be listening to the user voice to check if the user is speaking to the
    assistant.

    It is based on speech_recognition module, and it uses the Google recognition method.

    This thread will be producing messages to kafka when it recognizes a that the user is
    speaking to the assistant.
    """

    def __init__(self, valid_names: list, owner_uuid: str):
        super().__init__()
        logger.info("Starting recognizer")
        self.recognizer = sr.Recognizer()
        self.configure_recognizer()

        self.language = os.getenv("KATIA_LANGUAGE", "en-US")
        self.stopper_extra_words = literal_eval(
            os.getenv("RECOGNIZER_STOPPER_EXTRA_WORDS", "[]")
        )
        self.stopper_sentences = literal_eval(
            os.getenv("RECOGNIZER_STOPPER_SENTENCES", "[]")
        )
        self.valid_names = valid_names
        self.producer = KatiaProducer(topic=f"user-{owner_uuid}-interpreter")
        self.producer_for_speaker = KatiaProducer(
            topic=f"user-{owner_uuid}-speaker-stopper"
        )
        self.active = True
        logger.info("Recognizer started")

    def run(self) -> None:
        self.listen()

    def listen(self):
        """
        This method is the main method for the recognizer. It will continuously be
        listening to the user voice, and once it detects that the user is talking to the
        assistant it will send the recognized message to kafka
        :return:
        """
        with sr.Microphone() as source:
            logger.info("Waiting for adjustment of ambient noise")
            self.recognizer.adjust_for_ambient_noise(source)
            logger.info("Ambient noise adjustment done")
            while self.active:
                audio = self.recognizer.listen(source=source)
                try:
                    recognized = self.recognizer.recognize_google(
                        audio, language=self.language, show_all=True
                    )
                    logger.debug("recognizer catch: '%s'", recognized)
                    if self.called_me(recognized=recognized):
                        self.produce_messages(
                            next(iter(recognized.get("alternative", [])), {})
                            .get("transcript", "")
                            .lower()
                        )
                except sr.UnknownValueError:
                    continue
                except Exception as ex:
                    logger.error(
                        "Something unexpected happened during the listen",
                        extra={"error": ex},
                    )

    def produce_messages(self, recognized):
        """
        Method in charge of send to the producers:
            The interpreter for interpret the message.
            The speaker to stop talking if it was talking.
        :param recognized:
        :return:
        """

        if mixer.music.get_busy():
            self.producer_for_speaker.send_message(
                message_data={"source": "recognizer", "message": "Stop talking"}
            )
        if not self.should_assistant_stop_talking(recognized):
            logger.info("Will send the message: '%s' to the interpreter", recognized)
            self.producer.send_message(
                message_data={"source": "recognizer", "message": recognized}
            )

    def should_assistant_stop_talking(self, recognized: str):
        """
        Method to check if we should send a new message to the interpreter or just stop
        talking
        :param recognized:
        :return:
        """
        logger.debug("Try to check if should stop talking for sentence: '%s'", recognized)
        recognized = recognized.lower()
        recognized = recognized.replace(",", "").replace(".", "")

        recognized_regex_extra_words = re.compile(
            "|".join(map(re.escape, self.stopper_extra_words))
        )
        recognized = recognized_regex_extra_words.sub("", recognized)

        recognized_regex_sentences = re.compile(
            "|".join(map(re.escape, self.stopper_sentences))
        )
        recognized = recognized_regex_sentences.sub("", recognized)

        recognized_regex_valid_names = re.compile(
            "|".join(map(re.escape, self.valid_names))
        )
        recognized = recognized_regex_valid_names.sub("", recognized)
        recognized = recognized.strip()
        return_value = not bool(recognized)
        if return_value:
            logger.info("User request the assistant to stop talking")
        return return_value

    def called_me(self, recognized: dict):
        """
        This method check if the message recognized has any of the valid names for the
        assistant, to check if it has been called
        :param recognized:
        :return:
        """
        if recognized:
            for alternatives in recognized.get(
                "alternative",
                [
                    {},
                ],
            ):
                if any(
                    valid_name in alternatives.get("transcript", "").lower()
                    for valid_name in self.valid_names
                ):
                    return True
        return False

    def configure_recognizer(self):
        """
        Method to configure the recognizer according to the parameters set in the
        configuration.
        :return:
        """
        logger.info("Configuring recognizer")
        self.recognizer.energy_threshold = int(
            os.getenv("RECOGNIZER_ENERGY_THRESHOLD", "1")
        )
        self.recognizer.dynamic_energy_threshold = (
            os.getenv("RECOGNIZER_DYNAMIC_ENERGY_THRESHOLD", "False").lower() == "true"
        )
        self.recognizer.pause_threshold = float(
            os.getenv("RECOGNIZER_PAUSE_THRESHOLD", "0.4")
        )
        self.recognizer.phrase_threshold = float(
            os.getenv("RECOGNIZER_PHRASE_THRESHOLD", "0.8")
        )
        self.recognizer.non_speaking_duration = float(
            os.getenv("RECOGNIZER_NON_SPEAKING_DURATION", "0.2")
        )
        logger.info("Recognizer configured")

    def deactivate(self):
        """
        Method to deactivate the recognizer
        :return:
        """
        self.active = False
