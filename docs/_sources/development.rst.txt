.. _`Development`:

Development
===========
This section is intended for developers that want to create a fix or develop an enhancement to the CMPT221 course repository application.

Code of Conduct
---------------
Follow standard Python coding conventions, write clear commit messages, 
and ensure that all code changes are properly tested before committing. 
All pull requests should use descriptive titles and include a summary of changes.

Repository
----------
The repository for my CMPT221 Labs is on Github: https://github.com/BobbyMcD422/cmpt221

Development Environment
-----------------------
A `Python virtual environment`_ is recommended. Once the virtual environment is activated, clone the <application-name> repository and prepare the development environment with 

.. _Python virtual environment: https://virtualenv.pypa.io/en/latest/

.. code-block:: text

    $ git clone https://github.com/apndc/RestaurantProject.git
    $ cd RestaurantProject
    $ python -m venv .venv
    $ source .venv/bin/activate      # On Windows use: .venv\Scripts\activate
    $ pip install -r requirements.txt

This will install all local prerequisites needed for ``app.py`` to run.

Pytest
-------------------
Unit tests are developed using Pytest. To run the test suite, issue:

.. code-block:: text

    $ cd tests
    $ pytest <filename.py>

Build Documentation
-------------------
The Github pages site is used to publish documentation for the <application-name> application at <github-pages-link>

To build the documentation, issue:

.. code-block:: text
    
    $ cd docs
    $ make html
    # windows users without make installed use:
    $ make.bat html

The top-level document to open with a web-browser will be  ``docs/_build/html/index.html``.

To publish the page, copy the contents of the directory ``docs/_build/html`` into the branch
``gh-pages``. Then, commit and push to ``gh-pages``.