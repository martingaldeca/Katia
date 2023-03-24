import os
from logging import Logger, getLogger
from unittest import TestCase, mock

import freezegun
from botocore.exceptions import BotoCoreError

from katia.speaker import KatiaSpeaker


class KatiaSpeakerTestCase(TestCase):
    @staticmethod
    def deactivate_speaker(speaker_to_deactivate: KatiaSpeaker, data_to_return: dict):
        speaker_to_deactivate.deactivate()
        return data_to_return

    def test_init(self):
        with mock.patch.dict(
            os.environ,
            {
                "AWS_PROFILE_NAME": "test-profile",
                "AWS_VOICE_NAME": "test-voice-name",
            },
        ), mock.patch("katia.speaker.speaker.Session") as mock_session, mock.patch(
            "katia.speaker.speaker.mixer"
        ) as mock_mixer, mock.patch(
            "katia.speaker.speaker.KatiaConsumer"
        ) as mock_consumer, mock.patch(
            "katia.speaker.speaker.KatiaProducer"
        ) as mock_producer:
            speaker = KatiaSpeaker(owner_uuid="test-uuid")
            self.assertEqual(speaker.profile_name, "test-profile")
            self.assertEqual(speaker.voice, "test-voice-name")
            self.assertEqual(mock_session.call_count, 1)
            self.assertEqual(
                mock_session.call_args, mock.call(profile_name="test-profile")
            )
            self.assertEqual(mock_session().client.call_count, 1)
            self.assertEqual(mock_session().client.call_args, mock.call("polly"))
            self.assertEqual(mock_mixer.init.call_count, 1)
            self.assertEqual(mock_mixer.set_num_channels.call_count, 1)
            self.assertEqual(mock_consumer.call_count, 2)
            self.assertEqual(
                mock_consumer.call_args_list,
                [
                    mock.call(topic="user-test-uuid-speaker", group_id="test-uuid"),
                    mock.call(
                        topic="user-test-uuid-speaker-stopper", group_id="test-uuid"
                    ),
                ],
            )
            self.assertEqual(mock_producer.call_count, 1)
            self.assertEqual(
                mock_producer.call_args,
                mock.call(
                    topic="user-test-uuid-recognizer-last-speaking",
                    group_id="test-uuid"
                ),
            )

    def test_run(self):
        with mock.patch("katia.speaker.speaker.KatiaConsumer"), mock.patch(
            "katia.speaker.speaker.KatiaProducer"
        ), mock.patch.object(
            KatiaSpeaker, "speak"
        ) as mock_speak, mock.patch("katia.speaker.speaker.Session"), mock.patch(
            "katia.speaker.speaker.mixer"
        ):
            speaker = KatiaSpeaker(
                owner_uuid="test-uuid",
            )
            speaker.start()
        self.assertEqual(mock_speak.call_count, 1)

    def test_speak_message(self):
        def stop_waiting(mock_to_change):
            mock_to_change.return_value = False

        test_data_list = [
            ({"AudioStream": mock.MagicMock()}, 1, True, True, 1),
            ({"AudioStream": mock.MagicMock()}, 1, False, True, 0),
            ({"AudioStream": mock.MagicMock()}, 1, True, False, 0),
            ({"AudioStream": mock.MagicMock()}, 1, False, False, 0),
            ({"Not-AudioStream": None}, 0, True, True, 0),
        ]
        for test_data in test_data_list:
            with mock.patch.dict(
                os.environ,
                {
                    "AWS_VOICE_NAME": "test-voice-name",
                },
            ), mock.patch("katia.speaker.speaker.KatiaConsumer"), mock.patch(
                "katia.speaker.speaker.KatiaProducer"
            ), mock.patch(
                "katia.speaker.speaker.Session"
            ) as mock_session, mock.patch(
                "katia.speaker.speaker.mixer"
            ) as mock_mixer, mock.patch.object(
                KatiaSpeaker, "can_speak", new_callable=mock.PropertyMock
            ) as mock_can_speak, mock.patch(
                "katia.speaker.speaker.open"
            ), mock.patch(
                "time.sleep"
            ) as mock_sleep, mock.patch.object(
                getLogger("KatiaSpeaker"), "debug"
            ) as mock_logger_debug, mock.patch.object(
                KatiaSpeaker,
                'send_last_speak'
            ) as mock_send_last_speak:
                (
                    response,
                    mock_mixer_music_load_and_play_call_count,
                    get_busy,
                    can_speak,
                    mock_logger_debug_call_count,
                ) = test_data
                mock_session().client().synthesize_speech.return_value = response
                mock_mixer.music.get_busy.return_value = get_busy
                mock_can_speak.return_value = can_speak
                mock_sleep.side_effect = lambda _: stop_waiting(mock_can_speak)
                speaker = KatiaSpeaker(
                    owner_uuid="test-uuid",
                )
                speaker.speak_message("test-message")
                self.assertEqual(mock_session().client().synthesize_speech.call_count, 1)
                self.assertEqual(
                    mock_session().client().synthesize_speech.call_args,
                    mock.call(
                        Text="test-message",
                        OutputFormat="mp3",
                        VoiceId="test-voice-name",
                        Engine="neural",
                    ),
                )
                self.assertEqual(
                    mock_mixer.music.load.call_count,
                    mock_mixer_music_load_and_play_call_count,
                )
                self.assertEqual(
                    mock_mixer.music.play.call_count,
                    mock_mixer_music_load_and_play_call_count,
                )
                self.assertEqual(
                    mock_logger_debug.call_count, mock_logger_debug_call_count
                )
                self.assertEqual(mock_send_last_speak.call_count, 1)

    def test_can_speak(self):
        test_data_list = [
            ({"source": "recognizer"}, 1),
            ({"source": "not-recognizer"}, 0),
            (None, 0),
            ({"not-source": "recognizer"}, 0),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.speaker.speaker.KatiaConsumer"
            ) as mock_consumer, mock.patch("katia.speaker.speaker.Session"), mock.patch(
                "katia.speaker.speaker.mixer"
            ) as mock_mixer:
                data, mock_mixer_music_stop_call_count = test_data
                mock_consumer().get_data.return_value = data
                speaker = KatiaSpeaker(
                    owner_uuid="test-uuid",
                )
                self.assertTrue(speaker.can_speak)
                self.assertEqual(
                    mock_mixer.music.stop.call_count, mock_mixer_music_stop_call_count
                )

    def test_speak(self):
        test_data_list = [
            ({"source": "interpreter", "message": "test-message"}, 1),
            ({"source": "not-interpreter", "message": "test-message"}, 0),
            (None, 0),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.speaker.speaker.KatiaConsumer"
            ) as mock_consumer, mock.patch(
                "katia.speaker.speaker.KatiaProducer"
            ), mock.patch(
                "katia.speaker.speaker.Session"
            ), mock.patch.object(
                KatiaSpeaker, "wait_until_interpreter"
            ) as mock_wait_until_interpreter, mock.patch.object(
                KatiaSpeaker, "speak_message"
            ) as mock_speak_message, mock.patch(
                "katia.speaker.speaker.mixer"
            ):
                data, mock_speak_message_call_count = test_data
                speaker = KatiaSpeaker(
                    owner_uuid="test-uuid",
                )
                mock_consumer().get_data.side_effect = lambda: self.deactivate_speaker(
                    speaker_to_deactivate=speaker, data_to_return=data
                )
                speaker.speak()
                self.assertEqual(
                    mock_speak_message.call_count, mock_speak_message_call_count
                )
                self.assertEqual(mock_wait_until_interpreter.call_count, 1)

    def test_speak_with_error(self):
        with mock.patch(
            "katia.speaker.speaker.KatiaConsumer"
        ) as mock_consumer, mock.patch(
            "katia.speaker.speaker.KatiaProducer"
        ), mock.patch(
            "katia.speaker.speaker.Session"
        ), mock.patch.object(
            KatiaSpeaker, "wait_until_interpreter"
        ), mock.patch.object(
            KatiaSpeaker, "speak_message"
        ) as mock_speak_message, mock.patch.object(
            Logger, "error"
        ) as mock_error, mock.patch(
            "katia.speaker.speaker.mixer"
        ):
            speaker = KatiaSpeaker(
                owner_uuid="test-uuid",
            )
            mock_consumer().get_data.side_effect = lambda: self.deactivate_speaker(
                speaker_to_deactivate=speaker,
                data_to_return={"source": "interpreter", "message": "test-message"},
            )
            mock_speak_message.side_effect = BotoCoreError()
            speaker.speak()
            self.assertEqual(mock_error.call_count, 1)

    def test_wait_until_interpreter(self):
        test_data_list = [
            (
                "en-Us",
                "Hi! Let me configure some things. Once all is ready I will call you!",
            ),
            ("es-ES", "test-translation"),
        ]
        for test_data in test_data_list:
            with mock.patch("katia.speaker.speaker.Session"), self.subTest(
                test_data=test_data
            ), mock.patch("katia.speaker.speaker.KatiaConsumer"), mock.patch(
                "katia.speaker.speaker.KatiaProducer"
            ), mock.patch.dict(
                os.environ,
                {
                    "KATIA_LANGUAGE": test_data[0],
                },
            ), mock.patch(
                "katia.speaker.speaker.Translator"
            ) as mock_translator, mock.patch.object(
                KatiaSpeaker, "speak_message"
            ) as mock_speak_message, mock.patch(
                "katia.speaker.speaker.mixer"
            ):
                language, expected_value = test_data
                mock_translate = mock.MagicMock()
                mock_translate.text = "test-translation"
                mock_translator().translate.return_value = mock_translate
                speaker = KatiaSpeaker(
                    owner_uuid="test-uuid",
                )
                speaker.wait_until_interpreter()
                self.assertEqual(mock_speak_message.call_count, 1)
                self.assertEqual(
                    mock_speak_message.call_args, mock.call(message=expected_value)
                )

    def test_send_last_speak(self):
        with mock.patch(
            "katia.speaker.speaker.mixer"
        ), mock.patch(
            "katia.speaker.speaker.KatiaConsumer"
        ), mock.patch(
            "katia.speaker.speaker.KatiaProducer"
        ) as mock_producer, freezegun.freeze_time("1994-08-08 14:30:00"):
            speaker = KatiaSpeaker(
                owner_uuid="test-uuid",
            )
            speaker.send_last_speak()
            self.assertEqual(mock_producer().send_message.call_count, 1)
            self.assertEqual(
                mock_producer().send_message.call_args,
                mock.call(
                    message_data={
                        "source": "speaker",
                        "message": "1994-08-08T14:30:00"
                    }
                ),
            )
