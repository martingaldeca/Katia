import os
from logging import Logger
from unittest import TestCase, mock

from katia.interpreter import KatiaInterpreter


class KatiaInterpreterTestCase(TestCase):
    def test_init(self):
        with mock.patch.dict(
            os.environ,
            {
                "KATIA_LANGUAGE": "test-language",
                "OPENAI_KEY": "test-key",
                "OPENAI_MODEL": "test-model",
            },
        ), mock.patch(
            "katia.interpreter.interpreter.KatiaConsumer"
        ) as mock_consumer, mock.patch(
            "katia.interpreter.interpreter.KatiaProducer"
        ) as mock_producer, mock.patch.object(
            KatiaInterpreter, "initial_prompt", new_callable=mock.PropertyMock
        ) as mock_initial_prompt:
            mock_initial_prompt.return_value = "test-prompt"
            interpreter = KatiaInterpreter(
                name="test-name",
                owner_uuid="test-uuid",
                adjectives=("test-adjective1", "test-adjective2"),
            )
            self.assertEqual(interpreter.language, "test-language")
            self.assertEqual(interpreter.name, "test-name")
            self.assertEqual(
                interpreter.adjectives, ("test-adjective1", "test-adjective2")
            )
            self.assertEqual(mock_consumer.call_count, 1)
            self.assertEqual(
                mock_consumer.call_args, mock.call(topic="user-test-uuid-interpreter")
            )
            self.assertEqual(mock_producer.call_count, 1)
            self.assertEqual(
                mock_producer.call_args, mock.call(topic="user-test-uuid-speaker")
            )
            self.assertEqual(mock_initial_prompt.call_count, 1)
            self.assertEqual(
                interpreter.messages, [{"role": "system", "content": "test-prompt"}]
            )

    def test_init_without_openai_key(self):
        with self.assertRaises(EnvironmentError) as expected_error, mock.patch.object(
            Logger, "error"
        ) as mock_logger_error:
            KatiaInterpreter(
                name="test-name",
                owner_uuid="test-uuid",
                adjectives=("test-adjective1", "test-adjective2"),
            )
        self.assertEqual(mock_logger_error.call_count, 1)
        self.assertEqual(
            mock_logger_error.call_args,
            mock.call("Missing OPENAI_KEY for interpreter. This env value is mandatory"),
        )
        self.assertEqual(
            str(expected_error.exception),
            "Missing OPENAI_KEY for interpreter. This env value is mandatory",
        )

    def test_run(self):
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_KEY": "test-key",
            },
        ), mock.patch(
            "katia.interpreter.interpreter.KatiaProducer"
        ), mock.patch("katia.interpreter.interpreter.KatiaConsumer"), mock.patch.object(
            KatiaInterpreter, "interpret"
        ) as mock_interpret:
            interpreter = KatiaInterpreter(
                name="test-name",
                owner_uuid="test-uuid",
                adjectives=("test-adjective1", "test-adjective2"),
            )
            interpreter.start()
        self.assertEqual(mock_interpret.call_count, 1)

    def test_interpret_message(self):
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_KEY": "test-key",
            },
        ), mock.patch("katia.interpreter.interpreter.openai") as mock_openai, mock.patch(
            "katia.interpreter.interpreter.KatiaProducer"
        ) as mock_producer, mock.patch(
            "katia.interpreter.interpreter.KatiaConsumer"
        ), mock.patch.dict(
            os.environ,
            {
                "OPENAI_MODEL": "test-model",
            },
        ), mock.patch.object(
            KatiaInterpreter, "initial_prompt", new_callable=mock.PropertyMock
        ) as mock_initial_prompt:
            mock_initial_prompt.return_value = "test-prompt"
            mock_openai.ChatCompletion.create.return_value = {
                "choices": [{"message": {"content": "test-response"}}]
            }

            interpreter = KatiaInterpreter(
                name="test-name",
                owner_uuid="test-uuid",
                adjectives=("test-adjective1", "test-adjective2"),
            )
            interpreter.interpret_message("test-message")
            self.assertEqual(
                interpreter.messages,
                [
                    {"role": "system", "content": "test-prompt"},
                    {"role": "user", "content": "test-message"},
                    {"role": "assistant", "content": "test-response"},
                ],
            )
            self.assertEqual(mock_openai.ChatCompletion.create.call_count, 1)
            self.assertEqual(mock_producer().send_message.call_count, 1)
            self.assertEqual(
                mock_producer().send_message.call_args,
                mock.call(
                    message_data={"source": "interpreter", "message": "test-response"}
                ),
            )

    def test_interpret_message_with_exception(self):
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_KEY": "test-key",
            },
        ), mock.patch("katia.interpreter.interpreter.openai") as mock_openai, mock.patch(
            "katia.interpreter.interpreter.KatiaProducer"
        ) as mock_producer, mock.patch(
            "katia.interpreter.interpreter.KatiaConsumer"
        ), mock.patch.dict(
            os.environ,
            {
                "OPENAI_MODEL": "test-model",
                "KATIA_LANGUAGE": "test-language",
            },
        ), mock.patch.object(
            KatiaInterpreter, "initial_prompt", new_callable=mock.PropertyMock
        ) as mock_initial_prompt, mock.patch(
            "katia.interpreter.interpreter.Translator"
        ) as mock_translator, mock.patch.object(
            Logger, "error"
        ) as mock_logger_error:
            mock_initial_prompt.return_value = "test-prompt"
            mock_openai.ChatCompletion.create.side_effect = Exception("test-exception")
            mock_translate = mock.MagicMock()
            mock_translate.text = "ups-message"
            mock_translator().translate.return_value = mock_translate
            interpreter = KatiaInterpreter(
                name="test-name",
                owner_uuid="test-uuid",
                adjectives=("test-adjective1", "test-adjective2"),
            )
            interpreter.interpret_message("test-message")
            self.assertEqual(
                interpreter.messages,
                [
                    {"role": "system", "content": "test-prompt"},
                ],
            )
            self.assertEqual(mock_openai.ChatCompletion.create.call_count, 1)
            self.assertEqual(mock_producer().send_message.call_count, 1)
            self.assertEqual(
                mock_producer().send_message.call_args,
                mock.call(
                    message_data={"source": "interpreter", "message": "ups-message"}
                ),
            )
            self.assertEqual(mock_translator().translate.call_count, 1)
            self.assertEqual(
                mock_translator().translate.call_args,
                mock.call(
                    text=(
                        "ups, something went wrong. It seems that I can not understand "
                        "what are you saying"
                    ),
                    dest="test",
                ),
            )
            self.assertEqual(mock_logger_error.call_count, 1)
            self.assertEqual(
                mock_logger_error.call_args,
                mock.call(
                    "Something went wrong doing the interpretation of the message",
                    extra={"error": "test-exception", "message": "test-message"},
                ),
            )

    def test_interpret(self):
        def deactivate_interpreter(
            interpreter_to_deactivate: KatiaInterpreter, data_to_return: dict
        ):
            interpreter_to_deactivate.deactivate()
            return data_to_return

        test_data_list = [
            (None, 0),
            ({"source": "not-recognizer"}, 0),
            ({"source": "recognizer"}, 0),
            ({"source": "recognizer", "message": "test-message"}, 1),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.dict(
                os.environ,
                {
                    "OPENAI_KEY": "test-key",
                },
            ), mock.patch(
                "katia.interpreter.interpreter.KatiaConsumer"
            ) as mock_consumer, mock.patch(
                "katia.interpreter.interpreter.KatiaProducer"
            ), mock.patch.object(
                KatiaInterpreter, "ready_to_interpret"
            ) as mock_ready_to_interpret, mock.patch.object(
                KatiaInterpreter, "interpret_message"
            ) as mock_interpret_message:
                consumer_get_data_value, mock_interpret_message_call_count = test_data
                interpreter = KatiaInterpreter(
                    name="test-name",
                    owner_uuid="test-uuid",
                    adjectives=("test-adjective1", "test-adjective2"),
                )
                mock_consumer().get_data.side_effect = lambda: deactivate_interpreter(
                    interpreter_to_deactivate=interpreter,
                    data_to_return=consumer_get_data_value,
                )
                mock_consumer().get_data.return_value = consumer_get_data_value
                interpreter.interpret()
                self.assertEqual(mock_ready_to_interpret.call_count, 1)
                self.assertEqual(mock_consumer().get_data.call_count, 1)
                self.assertEqual(
                    mock_interpret_message.call_count, mock_interpret_message_call_count
                )

    def test_initial_prompt(self):
        test_data_list = [
            ("es-ES", 2, "test-initial test-adjective1 and test-adjective2 test-ending"),
            (
                "en-US",
                0,
                (
                    "You are a test-adjective1 and test-adjective2 assistant called "
                    "test-name. test-extra-description"
                ),
            ),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.dict(
                os.environ,
                {
                    "KATIA_LANGUAGE": test_data[0],
                    "OPENAI_KEY": "test-key",
                    "KATIA_EXTRA_DESCRIPTION": "test-extra-description",
                    "OPENAI_MODEL": "test-model",
                },
            ), mock.patch("katia.interpreter.interpreter.KatiaConsumer"), mock.patch(
                "katia.interpreter.interpreter.KatiaProducer"
            ), mock.patch.object(
                KatiaInterpreter, "translate_initial_prompt"
            ) as mock_translate_initial_prompt:
                (
                    language,
                    mock_translate_initial_prompt_call_count,
                    expected_prompt,
                ) = test_data
                mock_translate_initial_prompt.return_value = (
                    "test-initial ",
                    "and",
                    "test-ending ",
                )
                interpreter = KatiaInterpreter(
                    # This line will call the initial prompt also
                    name="test-name",
                    owner_uuid="test-uuid",
                    adjectives=("test-adjective1", "test-adjective2"),
                )
                self.assertEqual(interpreter.initial_prompt, expected_prompt)
                self.assertEqual(
                    mock_translate_initial_prompt.call_count,
                    mock_translate_initial_prompt_call_count,
                )

    def test_translate_initial_prompt(self):
        with mock.patch.dict(
            os.environ,
            {
                "KATIA_LANGUAGE": "test-language",
                "OPENAI_KEY": "test-key",
                "OPENAI_MODEL": "test-model",
            },
        ), mock.patch("katia.interpreter.interpreter.KatiaConsumer"), mock.patch(
            "katia.interpreter.interpreter.KatiaProducer"
        ), mock.patch.object(
            KatiaInterpreter, "initial_prompt", new_callable=mock.PropertyMock
        ), mock.patch(
            "katia.interpreter.interpreter.Translator"
        ) as mock_translator:
            interpreter = KatiaInterpreter(
                name="test-name",
                owner_uuid="test-uuid",
                adjectives=("test-adjective1", "test-adjective2"),
            )
            mock_translate = mock.MagicMock()
            mock_translate.text = "test-message"
            mock_translator().translate.return_value = mock_translate
            self.assertEqual(
                interpreter.translate_initial_prompt(
                    initial_text="text",
                    conjunction="text",
                    ending_text="text",
                ),
                ("test-message ", "test-message", "test-message"),
            )
            self.assertEqual(mock_translator().translate.call_count, 3)

    def test_ready_to_interpret(self):
        test_data_list = [
            ("es-ES", 1, "test-message"),
            ("en-US", 0, "All is ready! I will be your assistant!"),
        ]
        for test_data in test_data_list:
            with self.subTest(test_data=test_data), mock.patch.dict(
                os.environ,
                {
                    "KATIA_LANGUAGE": test_data[0],
                    "OPENAI_KEY": "test-key",
                    "OPENAI_MODEL": "test-model",
                },
            ), mock.patch("katia.interpreter.interpreter.KatiaConsumer"), mock.patch(
                "katia.interpreter.interpreter.KatiaProducer"
            ) as mock_producer, mock.patch.object(
                KatiaInterpreter, "initial_prompt", new_callable=mock.PropertyMock
            ), mock.patch(
                "katia.interpreter.interpreter.Translator"
            ) as mock_translator, mock.patch.object(
                KatiaInterpreter, "translate_initial_prompt"
            ):
                (
                    language,
                    mock_translator_call_count,
                    expected_starter_message,
                ) = test_data
                interpreter = KatiaInterpreter(
                    name="test-name",
                    owner_uuid="test-uuid",
                    adjectives=("test-adjective1", "test-adjective2"),
                )
                mock_translate = mock.MagicMock()
                mock_translate.text = "test-message"
                mock_translator().translate.return_value = mock_translate
                interpreter.ready_to_interpret()
                self.assertEqual(
                    mock_translator().translate.call_count, mock_translator_call_count
                )
                self.assertEqual(mock_producer().send_message.call_count, 1)
                self.assertEqual(
                    mock_producer().send_message.call_args,
                    mock.call(
                        message_data={
                            "source": "interpreter",
                            "message": expected_starter_message,
                        }
                    ),
                )
