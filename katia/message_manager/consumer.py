import json
import logging
import os

from confluent_kafka import Consumer, KafkaError

logger = logging.getLogger("Katia")


class KatiaConsumer(Consumer):
    """
    This is an overwrite of the confluent kafka consumer to be adapted to the Katia
    project.

    It will need a topic to consume as parameter in its instantiation, and will connect to
    the kafka service specified in the env values.
    """

    def __init__(self, topic: str, group_id: str):
        logger.info("Initializing consumer")
        self.broker_host = os.getenv("KAFKA_BROKER_URL")
        self.broker_port = os.getenv("KAFKA_BROKER_PORT")
        self.topic = topic
        super().__init__(
            {
                "bootstrap.servers": f"{self.broker_host}:{self.broker_port}",
                "group.id": group_id,
                "auto.offset.reset": "earliest",
            }
        )
        self.subscribe([self.topic])
        logger.info("Consumer has been initiated and subscribe to topic '%s'", self.topic)

    def get_message(self):
        """
        This method is in charge of consuming the different messages sent to the topic
        configured for the consumer.

        If there was an error it will log an error.
        :return:
        """
        message = self.poll(0.5)
        if message is None:
            return None
        if error := message.error():
            if error.code() != KafkaError._PARTITION_EOF:  # pylint: disable=W0212
                logger.error(
                    "Error while consuming kafka message", extra={"error": str(error)}
                )
            return None
        return message.value().decode("utf-8")

    def get_data(self):
        """
        This method will return the data transformed into a dict from kafka.
        It can return None if there was not any message in the topic.
        :return:
        """
        if message := self.get_message():
            return json.loads(message)
        return None
