Installation
============

Tachyonic Project netrino currently fully supports `CPython <https://www.python.org/downloads/>`__ 3.6.


CPython
--------

A universal wheel is available on PyPI for netrino. Installing it is as simple as:

.. code:: bash

    $ pip3 install netrino

Source Code
-----------

Tachyonic Project netrino infrastructure and code is hosted on `GitHub <https://github.com/TachyonicProject/netrino>`_.
Making the code easy to browse, download, fork, etc. Pull requests are always
welcome!

Clone the project like this:

.. code:: bash

    $ git clone https://github.com/TachyonicProject/netrino.git

Once you have cloned the repo or downloaded a tarball from GitHub, you
can install Tachyon like this:

.. code:: bash

    $ cd netrino
    $ pip3 install .

Or, if you want to edit the code, first fork the main repo, clone the fork
to your development area, and then run the following to install it using
symbolic linking, so that when you change your code, the changes will be
automatically available to your app without having to reinstall the package.

.. code:: bash

    $ cd netrino
    $ python3 setup.py develop

.. code:: bash

    $ python3 setup.py test
