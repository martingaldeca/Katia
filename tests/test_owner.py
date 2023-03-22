import os
from logging import Logger
from unittest import TestCase, mock

from katia.owner import Owner


class OwnerTestCase(TestCase):
    def test_init(self):
        test_data_list = [
            (True, 1),
            (False, 0),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.object(
                Owner, "create_kafka_topics"
            ) as mock_create_kafka_topics:
                create_topics, mock_create_kafka_topics_call_count = test_data
                owner = Owner(name="test-owner", create_topics=create_topics)
                self.assertEqual(
                    mock_create_kafka_topics.call_count,
                    mock_create_kafka_topics_call_count,
                )
                self.assertEqual(owner.name, "test-owner")
                self.assertIsNotNone(owner.uuid)

    def test_create_kafka_topics(self):
        test_data_list = [(None, 1, 0), (Exception(), 1, 1)]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.owner.AdminClient"
            ) as mock_admin_client, mock.patch(
                "katia.owner.NewTopic"
            ) as mock_new_topic, mock.patch.object(
                Logger, "error"
            ) as mock_logger_error, mock.patch.dict(
                os.environ,
                {
                    "KAFKA_BROKER_URL": "test-broker-url",
                    "KAFKA_BROKER_PORT": "test-broker-port",
                },
            ):
                mock_new_topic.return_value = "test-new-topic"

                (
                    side_effect,
                    mock_f_result_call_count,
                    mock_logger_error_call_count,
                ) = test_data
                mock_f = mock.MagicMock()
                mock_f.result.side_effect = side_effect
                mock_topics_created = mock.MagicMock()
                mock_topics_created.items.return_value = [("test-topic", mock_f)]
                mock_admin_client().create_topics.return_value = mock_topics_created
                owner = Owner(name="test-owner", create_topics=False)
                self.assertIsNone(owner.create_kafka_topics())
                self.assertEqual(mock_admin_client.call_count, 2)  # 2 because of the mock
                self.assertEqual(
                    mock_admin_client.call_args,
                    mock.call(
                        {
                            "bootstrap.servers": ("test-broker-url:test-broker-port"),
                        }
                    ),
                )
                self.assertEqual(mock_new_topic.call_count, 3)
                self.assertEqual(
                    mock_new_topic.call_args_list,
                    [
                        mock.call(
                            f"user-{owner.uuid}-speaker",
                            num_partitions=1,
                            replication_factor=1,
                        ),
                        mock.call(
                            f"user-{owner.uuid}-speaker-stopper",
                            num_partitions=1,
                            replication_factor=1,
                        ),
                        mock.call(
                            f"user-{owner.uuid}-interpreter",
                            num_partitions=1,
                            replication_factor=1,
                        ),
                    ],
                )
                self.assertEqual(mock_admin_client().create_topics.call_count, 1)
                self.assertEqual(
                    mock_admin_client().create_topics.call_args,
                    mock.call(["test-new-topic", "test-new-topic", "test-new-topic"]),
                )
                self.assertEqual(mock_f.result.call_count, mock_f_result_call_count)
                self.assertEqual(
                    mock_logger_error.call_count, mock_logger_error_call_count
                )
