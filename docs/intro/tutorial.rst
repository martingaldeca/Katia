.. _intro-tutorial:

===============
Katia Tutorial
===============

In this tutorial, we'll assume that Katia and its
:ref:`requirements <intro-installation-requirements>` are already installed on your system.
If that's not the case, see :ref:`intro-installation`.

.. _intro-tutorial-openai:

OPENAI setup
============

First of all you need a `OPENAI` account, as the interpreter is based on it. The value you
need is a token. You can obtain it once you created your account.

You can sign up from the official `platform openai page
<https://platform.openai.com/account>`_.

Once you are log in, you can get a new secret key from the `API Keys section
<https://platform.openai.com/account/api-keys>`_.

Remember, the `OPENAI API` is not free, try to configure the usage limits that suits with
you `here <https://platform.openai.com/account/billing/limits>`_.

.. _intro-tutorial-aws:

AWS setup
=========

Katia requires `AWS Polly <https://aws.amazon.com/es/polly/>`_ service to talk. So you
need to have an AWS account with polly configured and the permissions required.

You can follow the `AWS guide
<https://docs.aws.amazon.com/polly/latest/dg/getting-started.html>`_.

.. _intro-tutorial-basic_configuration:

Basic configuration
===================

We are going to create a simple assistant with a couple of configurations. You can get the
basic config directly from the `Github <https://github.com/martingaldeca/Katia>`_ files.

First of all we need to create a ``.env`` file. This is because Katia configuration is meant
to be set from environment values.

Here is an example of the ``.env`` that you can create:

.. code-block:: python

    # KAFKA CONFIGURATION
    KAFKA_BROKER_URL=<CHANGE_ME>
    KAFKA_BROKER_PORT=<CHANGE_ME>

    # General configuration
    KATIA_LANGUAGE=es-ES
    KATIA_MAIN_NAME=Katia
    KATIA_VALID_NAMES="['katia', 'catia', 'catya', 'katya', 'cati', 'katy', 'caty', 'kati']"
    KATIA_ADJECTIVES="[]"
    KATIA_EXTRA_DESCRIPTION="'You will always try to be very very concise.'"

    # Recognizer configuration
    RECOGNIZER_ENERGY_THRESHOLD=1
    RECOGNIZER_DYNAMIC_ENERGY_THRESHOLD=False
    RECOGNIZER_PAUSE_THRESHOLD=0.4
    RECOGNIZER_PHRASE_THRESHOLD=0.8
    RECOGNIZER_NON_SPEAKING_DURATION=0.2
    RECOGNIZER_STOPPER_EXTRA_WORDS="[]"
    RECOGNIZER_STOPPER_SENTENCES="['stop', 'now', 'talking', 'please']"

    # Interpreter configuration
    OPENAI_KEY=<CHANGE_ME>
    OPENAI_MODEL=gpt-4

    # Speaker configuration
    AWS_PROFILE_NAME=adminuser
    AWS_VOICE_NAME=Lucia
    AWS_ENGINE=neural

Here it is mandatory to change the ``OPENAI_KEY``, and not mandatory, but by default the
``AWS_PROFILE_NAME`` is ``adminuser``. So if this is not your profile change it also.

Also, remember to change the ``KAFKA_BROKER_URL`` and ``KAFKA_BROKER_PORT`` values to your
kafka broker.

You can explore the different values for the configuration in the
:ref:`configuration <configuration>` documentation

.. _intro-tutorial-run_kafka_in_local:

Run kafka in local
==================

This step is only needed if you want to run Katia pointing to a local kafka. If not, you
can go directly to :ref:`run <intro-tutorial-run>` section.

First of all you have to add these values to the ``.env`` file:

.. code-block:: python

    # KAFKA ENV
    ZOOKEEPER_CLIENT_PORT=2181
    ZOOKEEPER_TICK_TIME=2000
    KAFKA_ZOOKEEPER_CONNECT='zookeeper:2181'
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
    KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=3

Now you can use this ``docker-compose.yml`` and run kafka using docker:

.. code-block:: yaml

    version: '3.4'
    services:
      zookeeper:
        image: confluentinc/cp-zookeeper:7.0.1
        container_name: zookeeper
        hostname: zookeeper
        ports:
          - "2181:2181"
        env_file:
          - .env
        healthcheck:
          test: nc -z localhost 2181 || exit -1
          interval: 10s
          timeout: 5s
          retries: 3
          start_period: 10s
      broker:
        image: confluentinc/cp-kafka:7.0.1
        container_name: broker
        hostname: broker
        depends_on:
          zookeeper:
            condition: service_healthy
        links:
          - zookeeper
        ports:
          - "29092:29092"
          - "9092:9092"
          - "9101:9101"
        env_file:
          - .env

Then just run the following:

.. code-block:: bash

    docker compose build
    docker compose up --force-recreate -d

.. _intro-tutorial-run:

Run
===

Now we can create a simple ``main.py`` script to run Katia in your local:

.. code-block:: python

    from dotenv import load_dotenv

    from katia.katia import Katia
    from katia.logger_manager.logger import setup_logger
    from katia.owner import Owner

    if __name__ == "__main__":
        load_dotenv()
        setup_logger()

        owner = Owner(name="Katia User")
        Katia(owner=owner)

And voila! Katia will start talking to you!

.. image:: https://media.tenor.com/rrLadwcIvTIAAAAM/unicorn-magic.gif
    :align: center
    :alt: magic-meme
    :height: 300px

|
