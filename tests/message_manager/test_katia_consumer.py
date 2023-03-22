import os
from logging import Logger
from unittest import TestCase, mock

from confluent_kafka import KafkaError

from katia.message_manager.consumer import KatiaConsumer


class KatiaConsumerTestCase(TestCase):
    def test_init(self):
        with mock.patch.object(
            KatiaConsumer, "subscribe"
        ) as mock_subscribe, mock.patch.dict(
            os.environ,
            {
                "KAFKA_BROKER_URL": "test-broker-url",
                "KAFKA_BROKER_PORT": "test-broker-port",
            },
        ):
            consumer = KatiaConsumer(topic="test-topic")
            self.assertEqual(consumer.topic, "test-topic")
            self.assertEqual(consumer.broker_host, "test-broker-url")
            self.assertEqual(consumer.broker_port, "test-broker-port")
            self.assertEqual(mock_subscribe.call_count, 1)
            self.assertEqual(mock_subscribe.call_args, mock.call(["test-topic"]))

    def test_get_message(self):
        message_with_error_partition_eof = mock.MagicMock()
        partition_error = mock.MagicMock()
        partition_error.code.return_value = KafkaError._PARTITION_EOF
        message_with_error_partition_eof.error.return_value = partition_error
        message_with_error_not_partition_eof = mock.MagicMock()
        test_error = mock.MagicMock()
        test_error.code.return_value = "test-error"
        message_with_error_not_partition_eof.error.return_value = test_error
        message_valid = mock.MagicMock()
        message_valid.error.return_value = False
        message_valid.value.return_value = b"test-value"
        test_data_list = [
            (None, 0, None),
            (message_with_error_partition_eof, 0, None),
            (message_with_error_not_partition_eof, 1, None),
            (message_valid, 0, "test-value"),
        ]
        for test_data in test_data_list:
            with mock.patch.object(KatiaConsumer, "subscribe"), mock.patch.object(
                KatiaConsumer, "poll"
            ) as mock_poll, mock.patch.object(Logger, "error") as mock_logger_error:
                message, mock_logger_error_call_count, expected_response = test_data
                mock_poll.return_value = message

                consumer = KatiaConsumer(topic="test-topic")
                self.assertEqual(consumer.get_message(), expected_response)
                self.assertEqual(mock_poll.call_count, 1)
                self.assertEqual(
                    mock_logger_error.call_count, mock_logger_error_call_count
                )

    def test_get_data(self):
        test_data_list = [
            ('{"test": "test"}', {"test": "test"}),
            (None, None),
        ]
        for test_data in test_data_list:
            with mock.patch.object(KatiaConsumer, "subscribe"), mock.patch.object(
                KatiaConsumer, "get_message"
            ) as mock_get_message:
                message, expected = test_data
                mock_get_message.return_value = message
                consumer = KatiaConsumer(topic="test-topic")
                self.assertEqual(consumer.get_data(), expected)
