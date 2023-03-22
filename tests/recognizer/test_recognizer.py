import os
from logging import Logger
from unittest import TestCase, mock

from speech_recognition import UnknownValueError

from katia.recognizer import KatiaRecognizer


class KatiaRecognizerTestCase(TestCase):
    @staticmethod
    def deactivate_recognizer(
        recognizer_to_deactivate: KatiaRecognizer,
        data_to_return: str,
    ):
        recognizer_to_deactivate.deactivate()
        return data_to_return

    def test_init(self):
        with mock.patch(
            "katia.recognizer.recognizer.KatiaProducer"
        ) as mock_producer, mock.patch.dict(
            os.environ,
            {
                "KATIA_LANGUAGE": "en-US",
            },
        ), mock.patch.object(
            KatiaRecognizer, "configure_recognizer"
        ) as mock_configure_recognizer, mock.patch(
            "speech_recognition.Recognizer"
        ) as mock_recognizer:
            recognizer = KatiaRecognizer(
                valid_names=["test-name", "name-test"], owner_uuid="test-uuid"
            )
            self.assertEqual(recognizer.language, "en-US")
            self.assertEqual(recognizer.valid_names, ["test-name", "name-test"])
            self.assertEqual(mock_recognizer.call_count, 1)
            self.assertEqual(mock_configure_recognizer.call_count, 1)
            self.assertEqual(mock_producer.call_count, 2)
            self.assertEqual(
                mock_producer.call_args_list,
                [
                    mock.call(topic="user-test-uuid-interpreter"),
                    mock.call(topic="user-test-uuid-speaker-stopper"),
                ],
            )

    def test_run(self):
        with mock.patch("katia.recognizer.recognizer.KatiaProducer"), mock.patch.object(
            KatiaRecognizer, "listen"
        ) as mock_listen:
            recognizer = KatiaRecognizer(
                valid_names=["test-name", "name-test"], owner_uuid="test-uuid"
            )
            recognizer.start()
        self.assertEqual(mock_listen.call_count, 1)

    def test_listen(self):
        test_data_list = [
            (True, 1),
            (False, 0),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.recognizer.recognizer.KatiaProducer"
            ), mock.patch("speech_recognition.Microphone") as mock_microphone, mock.patch(
                "speech_recognition.Recognizer"
            ) as mock_recognizer, mock.patch.object(
                KatiaRecognizer, "called_me"
            ) as mock_called_me, mock.patch.object(
                KatiaRecognizer, "produce_messages"
            ) as mock_produce_messages:
                called_me, mock_produce_messages_call_count = test_data
                mock_recognizer().listen.side_effect = (
                    lambda source: self.deactivate_recognizer(
                        recognizer_to_deactivate=recognizer,
                        data_to_return="test-audio",
                    )
                )
                mock_recognizer().recognize_google.return_value = {}
                mock_called_me.return_value = called_me
                recognizer = KatiaRecognizer(
                    valid_names=["test-name", "name-test"], owner_uuid="test-uuid"
                )
                recognizer.listen()
                self.assertEqual(
                    mock_produce_messages.call_count, mock_produce_messages_call_count
                )
                self.assertEqual(mock_microphone.call_count, 1)
                self.assertEqual(mock_recognizer().adjust_for_ambient_noise.call_count, 1)
                self.assertEqual(mock_recognizer().listen.call_count, 1)
                self.assertEqual(mock_recognizer().recognize_google.call_count, 1)

    def test_listen_error(self):
        test_data_list = [
            (UnknownValueError(), 0),
            (Exception(), 1),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.recognizer.recognizer.KatiaProducer"
            ), mock.patch("speech_recognition.Microphone") as mock_microphone, mock.patch(
                "speech_recognition.Recognizer"
            ) as mock_recognizer, mock.patch.object(
                Logger, "error"
            ) as mock_logger_error:
                exception_raised, mock_logger_error_call_count = test_data
                mock_recognizer().listen.side_effect = (
                    lambda source: self.deactivate_recognizer(
                        recognizer_to_deactivate=recognizer,
                        data_to_return="test-audio",
                    )
                )
                mock_recognizer().recognize_google.side_effect = exception_raised
                recognizer = KatiaRecognizer(
                    valid_names=["test-name", "name-test"], owner_uuid="test-uuid"
                )
                recognizer.listen()
                self.assertEqual(mock_microphone.call_count, 1)
                self.assertEqual(mock_recognizer().adjust_for_ambient_noise.call_count, 1)
                self.assertEqual(mock_recognizer().listen.call_count, 1)
                self.assertEqual(mock_recognizer().recognize_google.call_count, 1)
                self.assertEqual(
                    mock_logger_error.call_count, mock_logger_error_call_count
                )

    def test_produce_messages(self):
        test_data_list = [
            (
                True,
                True,
                1,
                [
                    mock.call(
                        message_data={"source": "recognizer", "message": "Stop talking"}
                    )
                ],
            ),
            (False, True, 0, []),
            (
                True,
                False,
                2,
                [
                    mock.call(
                        message_data={"source": "recognizer", "message": "Stop talking"}
                    ),
                    mock.call(
                        message_data={"source": "recognizer", "message": "test-message"}
                    ),
                ],
            ),
            (
                False,
                False,
                1,
                [
                    mock.call(
                        message_data={"source": "recognizer", "message": "test-message"}
                    )
                ],
            ),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.recognizer.recognizer.mixer"
            ) as mock_mixer, mock.patch(
                "katia.recognizer.recognizer.KatiaProducer"
            ) as mock_producer, mock.patch.object(
                KatiaRecognizer, "should_assistant_stop_talking"
            ) as mock_should_assistant_stop_talking:
                (
                    mixer_busy,
                    should_assistant_stop_talking,
                    mock_producer_send_message_call_count,
                    mock_producer_send_message_call_args_list,
                ) = test_data
                mock_mixer.music.get_busy.return_value = mixer_busy
                mock_should_assistant_stop_talking.return_value = (
                    should_assistant_stop_talking
                )
                recognizer = KatiaRecognizer(
                    valid_names=["test-name", "name-test"], owner_uuid="test-uuid"
                )
                recognizer.produce_messages(recognized="test-message")
                self.assertEqual(
                    mock_producer().send_message.call_count,
                    mock_producer_send_message_call_count,
                )
                if mock_producer_send_message_call_count:
                    self.assertEqual(
                        mock_producer().send_message.call_args_list,
                        mock_producer_send_message_call_args_list,
                    )

    def test_should_assistant_stop_talking(self):
        recognizer_stopper_extra_words = ["test-extra-1", "test-extra-2"]
        recognizer_stopper_sentences = ["test-sentence-1", "test-sentence-2"]
        valid_names = ["test-name-1", "test-name-2"]
        test_data_list = [
            ("test-extra-1 test-sentence-1 test-name-1", True),
            ("   test-extra-2 test-sentence-2 test-name-2   ", True),
            ("test-extra-2 test-sentence-2 test-name-3", False),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.dict(
                os.environ,
                {
                    "RECOGNIZER_STOPPER_EXTRA_WORDS": str(recognizer_stopper_extra_words),
                    "RECOGNIZER_STOPPER_SENTENCES": str(recognizer_stopper_sentences),
                    "KATIA_VALID_NAMES": str(valid_names),
                },
            ):
                recognized, expected = test_data
                recognizer = KatiaRecognizer(
                    valid_names=valid_names, owner_uuid="test-uuid"
                )
                self.assertEqual(
                    recognizer.should_assistant_stop_talking(recognized=recognized),
                    expected,
                )

    def test_called_me(self):
        valid_names = ["test-name-1", "test-name-2"]
        test_data_list = [
            ({"alternative": [{"transcript": "test-name-1 do something"}]}, True),
            ({"alternative": [{"transcript": "test-name-2"}]}, True),
            ({"alternative": [{"transcript": "test-name-3"}]}, False),
            ({"alternative": [{"not-transcript": "test-name-3"}]}, False),
            ({"not-alternative": [{"transcript": "test-name-2"}]}, False),
            (None, False),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.dict(
                os.environ,
                {
                    "KATIA_VALID_NAMES": str(valid_names),
                },
            ):
                recognized, expected = test_data
                recognizer = KatiaRecognizer(
                    valid_names=valid_names, owner_uuid="test-uuid"
                )
                self.assertEqual(recognizer.called_me(recognized=recognized), expected)
