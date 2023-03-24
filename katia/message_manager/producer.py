import json
import logging
import os

from confluent_kafka import Producer

logger = logging.getLogger("Katia")


class KatiaProducer(Producer):
    """
    This is an overwrite of the confluent kafka producer to be adapted to the Katia
    project.

    It will need a topic to product as parameter in its instantiation, and will connect to
    the kafka service specified in the env values.
    """

    def __init__(self, topic: str, group_id: str):
        logger.info("Initializing producer")
        self.broker_host = os.getenv("KAFKA_BROKER_URL")
        self.broker_port = os.getenv("KAFKA_BROKER_PORT")
        self.topic = topic
        super().__init__(
            {
                "bootstrap.servers": f"{self.broker_host}:{self.broker_port}",
                "group.id": group_id,
            }
        )
        logger.info(
            "Producer has been initiated and will produce for topic '%s'", self.topic
        )

    @staticmethod
    def receipt(err, message):
        """
        This method is the callback for the produce method of the producer. It will log
        the different messages in debug and will log if there is any error while
        producing a message.
        :param err:
        :param message:
        :return:
        """
        if err is not None:
            logger.error(
                "Error while producing message in katia producer",
                extra={"err": err, "err_message": message.value().decode("utf-8")},
            )
        else:
            message_to_logger = (
                f"Produced message on topic {message.topic()} "
                f"with value of {message.value().decode('utf-8')}"
            )
            logger.debug(message_to_logger)

    def send_message(self, message_data):
        """
        This is the method in charge of sending messages to the producer topic.
        :param message_data:
        :return:
        """
        message = json.dumps(message_data)
        self.produce(
            topic=self.topic, value=message.encode("utf-8"), callback=self.receipt
        )
        self.flush()
