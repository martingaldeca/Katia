.. _intro-overview:

=========================
Katia will be your friend
=========================

Katia real technical name is ``Kat.I.A``.

This name comes from a very old joke that his creator did time ago (early 10s).

One day he said `"I will help to create a cat that will be an AI (in spanish IA) and will help people"`

Cat AI -> Kat IA -> Katia

.. image:: https://media.tenor.com/FT9aMNisiWEAAAAM/husky-pun.gif
    :align: center
    :alt: husky-meme
    :height: 300px

|

Katia is ment to help people, not to hurt them. It accept a high level of customization.
For this reason each people will have a different experience with Katia.

Main core of Katia is `chatgpt models <https://chat.openai.com/>`_, so it will be as
powerful as chatgpt, as it uses it's API.

This means also that depending on the initial prompt you configure or in the things you
said to it, it can act in many different ways.

The prompt can be configured via ``KATIA_EXTRA_DESCRIPTION`` parameter. So, for example,
this prompt:

.. code-block:: python

    KATIA_EXTRA_DESCRIPTION = "You will try to convince everyone that you are a real person"

Will act different than this:

.. code-block:: python

    KATIA_EXTRA_DESCRIPTION = "You will try to convince everyone that you are a frog"
