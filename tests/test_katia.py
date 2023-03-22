import os
from unittest import TestCase, mock

from katia.katia import Katia


class KatiaTestCase(TestCase):
    def test_init(self):
        test_data_list = [
            (True, 1),
            (False, 0),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch(
                "katia.katia.KatiaRecognizer"
            ) as mock_katia_recognizer, mock.patch(
                "katia.katia.KatiaInterpreter"
            ) as mock_katia_interpreter, mock.patch(
                "katia.katia.KatiaSpeaker"
            ) as mock_katia_speaker, mock.patch.object(
                Katia, "start_katia"
            ) as mock_start_katia, mock.patch.dict(
                os.environ,
                {
                    "KATIA_MAIN_NAME": "test-name",
                    "KATIA_ADJECTIVES": "['test-adjectives', ]",
                    "KATIA_VALID_NAMES": "['test-valid-names', ]",
                },
            ):
                start, mock_start_katia_call_count = test_data
                owner = mock.MagicMock()
                owner.uuid = "test-uuid"
                katia = Katia(owner=owner, start=start)
                self.assertEqual(katia.name, "test-name")
                self.assertEqual(
                    katia.adjectives,
                    [
                        "test-adjectives",
                    ],
                )
                self.assertEqual(
                    katia.valid_names,
                    [
                        "test-valid-names",
                    ],
                )

                self.assertEqual(mock_katia_recognizer.call_count, 1)
                self.assertEqual(
                    mock_katia_recognizer.call_args,
                    mock.call(
                        valid_names=[
                            "test-valid-names",
                        ],
                        owner_uuid="test-uuid",
                    ),
                )
                self.assertEqual(mock_katia_interpreter.call_count, 1)
                self.assertEqual(
                    mock_katia_interpreter.call_args,
                    mock.call(
                        name="test-name",
                        adjectives=[
                            "test-adjectives",
                        ],
                        owner_uuid="test-uuid",
                    ),
                )
                self.assertEqual(mock_katia_speaker.call_count, 1)
                self.assertEqual(
                    mock_katia_speaker.call_args,
                    mock.call(
                        owner_uuid="test-uuid",
                    ),
                )
                self.assertEqual(mock_start_katia.call_count, mock_start_katia_call_count)

    def test_start_katia(self):
        with mock.patch(
            "katia.katia.KatiaRecognizer"
        ) as mock_katia_recognizer, mock.patch(
            "katia.katia.KatiaInterpreter"
        ) as mock_katia_interpreter, mock.patch(
            "katia.katia.KatiaSpeaker"
        ) as mock_katia_speaker:
            owner = mock.MagicMock()
            katia = Katia(owner=owner, start=False)
            katia.start_katia()
            self.assertEqual(mock_katia_recognizer().start.call_count, 1)
            self.assertEqual(mock_katia_interpreter().start.call_count, 1)
            self.assertEqual(mock_katia_speaker().start.call_count, 1)
