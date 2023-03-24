import logging
import os
import uuid

from confluent_kafka.admin import AdminClient, NewTopic

logger = logging.getLogger("KatiaOwner")


class Owner:
    """
    Basic info about the owner of the assistant
    """

    def __init__(self, name: str, create_topics: bool = True):
        logger.info("Initializing owner")
        self.name = name
        self.uuid = uuid.uuid4().hex
        if create_topics:
            self.create_kafka_topics()
        logger.info("Owner initialized")

    def create_kafka_topics(self):
        """
        Method to create the kafka topics associated to the owner
        :return:
        """
        logger.info("Creating topics for owner")
        admin_client = AdminClient(
            {
                "bootstrap.servers": (
                    f"{os.getenv('KAFKA_BROKER_URL')}:{os.getenv('KAFKA_BROKER_PORT')}"
                ),
            }
        )
        new_topics = [
            NewTopic(topic, num_partitions=1, replication_factor=1)
            for topic in [
                f"user-{self.uuid}-speaker",
                f"user-{self.uuid}-speaker-stopper",
                f"user-{self.uuid}-interpreter",
                f"user-{self.uuid}-recognizer-last-speaking"
            ]
        ]
        topic_creation = admin_client.create_topics(new_topics)
        # Wait for each operation to finish.
        for topic, topic_creation_result in topic_creation.items():
            try:
                topic_creation_result.result()  # The result itself is None
                logger.info("Topic '%s' created", topic)
            except Exception as ex:
                logger.error("Failed to create topic", extra={"topic": topic, "ex": ex})
