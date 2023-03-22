import os
from logging import Logger
from unittest import TestCase, mock

from katia.message_manager import KatiaProducer


class ProducerTestCase(TestCase):
    def test_init(self):
        with mock.patch.dict(
            os.environ,
            {
                "KAFKA_BROKER_URL": "test-broker-url",
                "KAFKA_BROKER_PORT": "test-broker-port",
            },
        ):
            producer = KatiaProducer(topic="test-topic")
            self.assertEqual(producer.topic, "test-topic")
            self.assertEqual(producer.broker_host, "test-broker-url")
            self.assertEqual(producer.broker_port, "test-broker-port")

    def test_receipt(self):
        message = mock.MagicMock()
        message.value.return_value = b"test-message"
        test_data_list = [(None, 0), ("test-error", 1)]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.object(
                Logger, "error"
            ) as mock_logger_error:
                err, mock_logger_error_call_count = test_data
                KatiaProducer.receipt(err=err, message=message)
                self.assertEqual(
                    mock_logger_error.call_count, mock_logger_error_call_count
                )

    def test_send_message(self):
        with mock.patch.object(
            KatiaProducer, "produce"
        ) as mock_produce, mock.patch.object(KatiaProducer, "flush") as mock_flush:
            producer = KatiaProducer(topic="test-topic")
            message_data = {"test": "test"}
            producer.send_message(message_data=message_data)
            self.assertEqual(mock_produce.call_count, 1)
            self.assertEqual(
                mock_produce.call_args,
                mock.call(
                    topic="test-topic",
                    value=b'{"test": "test"}',
                    callback=producer.receipt,
                ),
            )
            self.assertEqual(mock_flush.call_count, 1)
