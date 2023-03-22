.. _intro-installation:

==================
Installation guide
==================

.. _intro-installation-python_versions:

Supported Python versions
=========================

Katia requires Python ``3.8+``. It will be continuously updated, so it will be supporting
the latest's versions of python.

.. _intro-installation-requirements:

Requirements
============
There ara a few of requirements to run Katia without problems.

First of all, Katia uses ``kafka``, so you need a kafka url where the topics for the
correct work can be created.

Also it uses voice recognition, so you need all the dependencies in your system for that.
This means you need the following:

* ``ffmpeg``
* ``python3-pyaudio``
* ``libasound-dev``

Katia had been tested only in `Linux`, so it is not sure if it will work in `Windows` or
`Mac`.

If you are using that OS and you have problems, feel free to open an issue and try to
create a PR that solve it.

You can check how to install ``Pyaudio`` in different OS
`here <https://pypi.org/project/PyAudio/>`_

.. _intro-installation-installing_katia:

Installing Katia
=================

You can install Katia and its dependencies using from ``PyPI`` using pip::

    pip install katia

We strongly recommend that you install Katia in
:ref:`a dedicated virtualenv <intro-installation-using_virtualenv>`, to avoid conflicting
with your system packages.

.. _intro-installation-using_virtualenv:

Using a virtual environment (recommended)
-----------------------------------------

TL;DR: We recommend installing Katia inside a virtual environment on all platforms.

Python packages can be installed either globally (a.k.a system wide),
or in user-space. We do not recommend installing Katia system wide.

Instead, we recommend that you install Katia within a so-called
"virtual environment" (:mod:`venv`).
Virtual environments allow you to not conflict with already-installed Python
system packages (which could break some of your system tools and scripts),
and still install packages normally with ``pip`` (without ``sudo`` and the likes).

See :ref:`tut-venv` on how to create your virtual environment.

Once you have created a virtual environment, you can install Katia inside it with ``pip``,
just like any other Python package.
