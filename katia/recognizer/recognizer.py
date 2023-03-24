import datetime
import logging
import os
import re
from ast import literal_eval
from threading import Thread

import speech_recognition as sr
from pygame import mixer

from katia.message_manager import KatiaProducer
from katia.message_manager.consumer import KatiaConsumer

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
        self.continue_conversation_delay_in_seconds = int(
            os.getenv("RECOGNIZER_CONTINUE_CONVERSATION_DELAY_IN_SECONDS", "30")
        )
        self.gap_continue_conversation_in_seconds = int(
            os.getenv("RECOGNIZER_GAP_CONTINUE_CONVERSATION_IN_SECONDS", "3")
        )
        self.valid_names = valid_names
        self.producer = KatiaProducer(
            topic=f"user-{owner_uuid}-interpreter",
            group_id=owner_uuid
        )
        self.producer_stopper = KatiaProducer(
            topic=f"user-{owner_uuid}-speaker-stopper", group_id=owner_uuid
        )
        self.consumer_last_speaking = KatiaConsumer(
            topic=f"user-{owner_uuid}-recognizer-last-speaking", group_id=owner_uuid
        )
        self.last_speaking = datetime.datetime.now()
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
                    self.get_last_speaking()
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
        Method in charge of sending messages to the producers:
            Stop the speaker if the user directly asks to do so while Katia is speaking
            Send the recognized message to the interpreter if Katia is not speaking
        :param recognized:
        :return:
        """
        is_speaking = mixer.music.get_busy()
        if is_speaking and self.should_assistant_stop_talking(recognized):
            # Stop the speaker if the user directly asks to do so while Katia is speaking
            self.producer_stopper.send_message(
                message_data={"source": "recognizer", "message": "Stop speaking"}
            )
        if not is_speaking and not self.should_assistant_stop_talking(recognized):
            # Send the recognized message to the interpreter if Katia is not speaking
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
        logger.debug(
            "Try to check if should stop speaking for sentence: '%s'",
            recognized
        )
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
            logger.info("User request the assistant to stop speaking")
        return return_value

    def called_me(self, recognized: dict):
        """
        This method check if the message recognized has any of the valid names for the
        assistant, to check if it has been called.

        Also, if the gap between the last time katia spoke and now are small enough. With
        this you can have a "normal" conversation with her.

        :param recognized:
        :return:
        """
        if (
            recognized and
            self.continue_conversation_delay_in_seconds >
            (
                datetime.datetime.now() - self.last_speaking
            ).total_seconds() > self.gap_continue_conversation_in_seconds
        ):
            return True
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

    def get_last_speaking(self):
        """
        Get the latest speaking from the speaker and save it.
        """
        data = self.consumer_last_speaking.get_data()
        if data and (source := data.get("source", None)):
            if source == "speaker":
                logger.info(
                    "Received when katia stopped talking"
                )
                self.last_speaking = datetime.datetime.strptime(
                    data['message'],
                    "%Y-%m-%dT%H:%M:%S.%f"
                )
