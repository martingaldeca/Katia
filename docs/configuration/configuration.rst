.. _configuration:

===================
Katia Configuration
===================

You can configure Katia with different parameters that will allow you to create different
assistants with different behaviours.

.. _configuration-docker_configuration:

Docker configuration
====================

If you are running in local kafka, using the
:ref:`associated tutorial<intro-tutorial-run_kafka_in_local>`, you can customize some
aspects of kafka deployment.

.. _configuration-docker_configuration-zookeeper_configuration:

Zookeeper configuration
-----------------------

* ``ZOOKEEPER_CLIENT_PORT``:

    Instructs ZooKeeper where to listen for connections by clients such as Apache Kafka®.

* ``ZOOKEEPER_TICK_TIME``:

    This is only required when running in clustered mode. Sets the server ID in the
    ``myid`` file, which consists of a single line that contains only the text of that
    machine’s ID. For example, the ``myid`` of server 1 would only contain the text "1".
    The ID must be unique within the ensemble and should have a value between 1 and 255.

.. _configuration-docker_configuration-kafka_configuration:

Kafka configuration
-------------------

* ``KAFKA_ZOOKEEPER_CONNECT``:

    Instructs Kafka how to get in touch with ZooKeeper.

* ``KAFKA_LISTENER_SECURITY_PROTOCOL_MAP``:

    Defines key/value pairs for the security protocol to use, per listener name. This is
    equivalent to the ``listener.security.protocol.map`` configuration parameter in the
    server properties file (``<path-to-confluent>/etc/kafka/server.properties``).

* ``KAFKA_ADVERTISED_LISTENERS``:

    A comma-separated list of listeners with their the host/IP and port. This is the
    metadata that is passed back to clients. This is equivalent to the
    ``advertised.listeners`` configuration parameter in the server properties file
    (``<path-to-confluent>/etc/kafka/server.properties``).

* ``KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR``:

    This setting defines the replication factor of the topic used to store the consumers
    offset. In the default case this is set to ``1``. So the consumer offsets for a
    particular topic will only be present on a single node. If that node goes down,
    consumers will lose track of where they are, since they can’t update the consumer
    offsets.

* ``KAFKA_TRANSACTION_STATE_LOG_MIN_ISR``:

    The minimum ISR for this topic. This is equivalent to the
    ``transaction.state.log.min.isr`` configuration parameter in the server properties
    file (``<path-to-confluent>/etc/kafka/server.properties``).

* ``KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR``:

    The replication factor for the transaction topic (set higher to ensure availability).
    Internal topic creation will fail until the cluster size meets this replication factor
    requirement. This is equivalent to the ``transaction.state.log.replication.factor``
    configuration parameter in the server properties file
    (``<path-to-confluent>/etc/kafka/server.properties``).

* ``KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS``:

    The amount of time the group coordinator will wait for more consumers to join a new
    group before performing the first rebalance. A longer delay means potentially fewer
    rebalances, but increases the time until processing begins. This is equivalent to the
    ``group.initial.rebalance.delay.ms`` configuration parameter in the server properties
    file (``<path-to-confluent>/etc/kafka/server.properties``).

.. _configuration-katia_configuration:


Katia service configuration
===========================

.. _configuration-katia_configuration-kafka_configuration:

Kafka configuration
-------------------

Both this configuration fields are mandatory, and Katia will not work unless she can
connect to a kafka broker. As Katia is based on an :ref:`architecture
<intro-architecture-schema>` centered in kafka communication between services.

* ``KAFKA_BROKER_URL``: **MANDATORY**

    This is your kafka url.

* ``KAFKA_BROKER_PORT``: **MANDATORY**

    This is your kafka port.


.. _configuration-katia_configuration-general_configuration:

General configuration
---------------------

* ``KATIA_LANGUAGE``:

    Language for Katia. You can use the standard codes for languages from
    `ISO 639-1 <https://es.wikipedia.org/wiki/ISO_639-1>`_ and from
    `ISO 3166-1 <https://es.wikipedia.org/wiki/ISO_3166-1>`_.

    ::

        en-US
        en-EN
        es-ES
        ...

* ``KATIA_MAIN_NAME``:

    The name of the interpreter. It is used to generate the interpreter personality.
    As it will be the name used to define itself. We like ``Katia``, but you can
    configure with the name you want for your assistant 🙂

* ``KATIA_VALID_NAMES``:

    Sometimes the recognizer does not recognize well the name of the assistant, so here
    you can add the different valid pronunciations/names for your assistant. For example,
    for ``Katia`` should be also valid this list:
    ``"['katia', 'catia', 'catya', 'katya', 'cati', 'katy', 'caty', 'kati']"``

.. _configuration-katia_configuration-extra_prompt:

Extra prompt
------------

By default the prompt form Katia is very easy: ``You are a assistant called {name}.``.
But, you can add extra things to this prompt, like adjectives for the assistant, or extra
text.

For that purpose you can use the following configurations:

* ``KATIA_ADJECTIVES``:

    This will be a list of adjectives that will be placed before the assistant word in
    the initial prompt. So, for example ``"['funny', 'helpful', 'kind']"`` will produce
    the following prompt: ``You are a funny, helpful and kind assistant called {name}.``

* ``KATIA_EXTRA_DESCRIPTION``:

    This is parameter you want if you want to add extra behaviours for your assistant.
    It is a free text and you can add things like: ``You will always be very concise.``
    and it will produce the following prompt:
    ``You are a assistant called {name}. You will always be very concise.``

    You can add very complex (and funny) things, like for example:
    ``You will always speak in verse with assonant rhyme.``, or
    ``you're always rapping like you're from a fucked up neighborhood, saying a lot of
    swear words.``.

    We do not encourage to set up this last prompt if you are going to show
    Katia to your granny, unless your granny is a very tough granny. 👵

.. _configuration-katia_configuration-recognizer_configuration:

Recognizer configuration
------------------------

* ``RECOGNIZER_ENERGY_THRESHOLD``:

   This is the minimum audio energy to consider for recording. Under 'ideal' conditions
    (such as in a quiet room), values between 0 and 100 are considered silent or ambient,
    and values 300 to about 3500 are considered speech.

* ``RECOGNIZER_DYNAMIC_ENERGY_THRESHOLD``:

    With ``RECOGNIZER_DYNAMIC_ENERGY_THRESHOLD`` set to ``'True'``, Katia will
    continuously try to re-adjust the energy threshold to match the environment based on
    the ambient noise level at that time.

* ``RECOGNIZER_PAUSE_THRESHOLD``:

    Seconds of non-speaking audio before a phrase is considered complete for Katia.

* ``RECOGNIZER_PHRASE_THRESHOLD``:

    Minimum seconds of speaking audio before we consider the speaking audio a phrase -
    values below this are ignored (for filtering out clicks and pops).

* ``RECOGNIZER_NON_SPEAKING_DURATION``:

    Seconds of non-speaking audio to keep on both sides of the recording.

* ``RECOGNIZER_STOPPER_EXTRA_WORDS``:

    List of words that can be added to the stopper sentences. This field is complementary
    to ``RECOGNIZER_STOPPER_SENTENCES``. And it is ment to work together.

* ``RECOGNIZER_STOPPER_SENTENCES``:

    List of sentences to use for katia to stop talking. This field is complementary to
    ``RECOGNIZER_STOPPER_EXTRA_WORDS``. For example, you can use this values:

    ::

        RECOGNIZER_STOPPER_EXTRA_WORDS="['hey', 'please']"
        RECOGNIZER_STOPPER_SENTENCES="['stop talking', 'shut up']"

    And if you say something like: ``Hey Katia, stop talking please`` it will stop. But
    for something like ``Hey catia, can you shut up now please?`` it will not work. You
    should add ``can``, ``you`` and ``now`` to ``RECOGNIZER_STOPPER_EXTRA_WORDS``.

.. _configuration-katia_configuration-interpreter_configuration:

Interpreter configuration
-------------------------

* ``OPENAI_KEY``: **MANDATORY**

    This is your API key from openai. You can follow the tutorial about how to get one in
    the :ref:`OPENAI setup tutorial <intro-tutorial-openai>`

    If the API key is not valid or if it is not set at all you will se an exception.

* ``OPENAI_MODEL``:

    This is the model you want to use for chatgpt. You can check which ones you can use in
    the `official documentation of OPENAI
    <https://platform.openai.com/docs/models/overview>`_.

.. _configuration-katia_configuration-speaker_configuration:

Speaker configuration
---------------------

* ``AWS_PROFILE_NAME``:

    This is your AWS profile for the speaker. You can follow the :ref:`tutorial
    <intro-tutorial-aws>` to get this well configured.

* ``AWS_VOICE_NAME``:

    This is the model you want to use from Polly for your voice. You can pick one of the
    `available ones <https://docs.aws.amazon.com/polly/latest/dg/voicelist.html>`_
    provided by AWS Polly. (``Name/ID`` value)

    Remember that some of the voices does not support neural voice, so make sure you
    configure this value according to the ``AWS_ENGINE``

* ``AWS_ENGINE``:

    This is the type of engine you want to use for AWS Polly. The two values accepted are
    ``neural`` or ``standard``. You can check the differences `here
    <https://docs.aws.amazon.com/polly/latest/dg/NTTS-main.html>`_.





