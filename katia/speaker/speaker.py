import logging
import os
import time
from contextlib import closing
from threading import Thread

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from googletrans import Translator
from pygame import mixer

from katia.message_manager.consumer import KatiaConsumer

logger = logging.getLogger("KatiaSpeaker")


class KatiaSpeaker(Thread):
    """
    This is the main speaker. It will run in a separate thread, and it will continuously
    be listening kafka topic to check if the interpreter sent something to reproduce.

    It is based on AWS polly service, so you will need to be logged in AWS and have a user
    with the right permissions if you want this to work.
    """

    def __init__(self, owner_uuid: str):
        super().__init__()
        logger.info("Starting speaker")
        self.profile_name = os.getenv("AWS_PROFILE_NAME", "adminuser")
        self.voice = os.getenv("AWS_VOICE_NAME", "Lucia")
        self.engine = os.getenv("AWS_ENGINE", "neural")
        self.session = Session(profile_name=self.profile_name)
        self.polly = self.session.client("polly")
        self.language = os.getenv("KATIA_LANGUAGE", "en-US")
        mixer.init()
        mixer.set_num_channels(1)

        self.consumer = KatiaConsumer(topic=f"user-{owner_uuid}-speaker")
        self.stopper_consumer = KatiaConsumer(topic=f"user-{owner_uuid}-speaker-stopper")
        self.active = True
        logger.info("Speaker started")

    def run(self) -> None:
        self.speak()

    def speak_message(self, message: str):
        """
        This is the method that the speaker has to reproduce the interpreter messages.
        First it will create a response.mp3 file using the polly client from AWS.
        Then it will reproduce it using the mixer reproducer from pygame.

        Even if there is multiple messages needed to be reproduced, it will wait until the
        previous one was completed.
        :param message:
        :return:
        """
        response = self.polly.synthesize_speech(
            Text=message,
            OutputFormat="mp3",
            VoiceId=self.voice,
            Engine=self.engine,
        )
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                output = os.path.join("./", "response.mp3")
                with open(output, "wb") as file:
                    file.write(stream.read())
            mixer.music.load("./response.mp3")
            mixer.music.play()
            while mixer.music.get_busy() and self.can_speak:
                logger.debug("Waiting to end sentence")
                time.sleep(1)

    @property
    def can_speak(self):
        """
        Katia will always be able to speak new things. But if recognizer sent something
        new she will stop talking until process the new.
        :return:
        """
        data = self.stopper_consumer.get_data()
        if data and (source := data.get("source", None)):
            if source == "recognizer":
                logger.debug(
                    "Stop talking because the recognizer recognized something new"
                )
                mixer.music.stop()
        return True

    def speak(self):
        """
        This is the main method for the speaker. It will continuously be listening to a
        kafka topic to check if the interpreter sent something that needs to be said.
        :return:
        """
        self.wait_until_interpreter()
        while self.active:
            data = self.consumer.get_data()
            if data and (source := data.get("source", None)) and source == "interpreter":
                try:
                    self.speak_message(data.get("message", ""))
                except (BotoCoreError, ClientError) as error:
                    logger.error("Error trying to speak", extra={"error": error})

    def wait_until_interpreter(self):
        """
        Method that will notice the user that he needs to wait until all is configured.
        :return:
        """
        logger.info("Waiting for interpreter to be ready")
        starter_message = (
            "Hi! Let me configure some things. Once all is ready I will call you!"
        )
        if "en" not in self.language:
            translator = Translator()
            language_to_use = self.language.split("-", maxsplit=1)[0]
            starter_message = translator.translate(
                text=starter_message,
                dest=language_to_use,
            ).text
        self.speak_message(message=starter_message)

    def deactivate(self):
        """
        Method to deactivate the speaker
        :return:
        """
        self.active = False
