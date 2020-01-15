# mkpreview
A tool to create video previews of movie files

==================
mkpreview
==================



Get Started!
------------
Here’s how to set up *mkpreview* for local environment.

1- Clone the *mkpreview* locally:

.. code-block:: console

    $ git clone git@github.com:/mkpreview.git

2- Install your local copy into a *virtualenv*. Assuming you have *virtualenvwrapper* installed, this is how you set up the package for local development:

.. code-block:: console

    $ sudo make boostrap
    $ mkvirtualenv mkpreview
    $ pip install -r requirements/dev.txt

3- How to enable/disable virtualenv

.. code-block:: console

    $ workon mkpreview
    $ ...
    $ deactivate
