# new-project-template
A template repo for new CL projects

{{NEW-PROJECT}}
=========

{{NEW-PROJECT}} is an open source repository to ...
It was built for use with Courtlistener.com.

Its main goal is to ...
It incldues mechanisms to ...

Further development is intended and all contributors, corrections and additions are welcome.

Background
==========

Free Law Project built this ...  This project represents ...  
We believe to be the ....

Quickstart
===========

You can feed in a X as ... .. ... 

::

        IMPORTS

        CALL EXAMPLE

        returns:
          ""EXAMPLE OUTPUT



Some Notes ...
======================
Somethings to keep in mind as ....

1. ...
2. ...


Fields
======

1. :code:`id` ==> string; Courtlistener Court Identifier
2. :code:`court_url` ==> string; url for court website
3. :code:`regex` ==>  array; regexes patterns to find courts


Installation
============

Installing {{NEW-PROJECT}} is easy.

    ::

        pip install {{NEW-PROJECT}}


Or install the latest dev version from github

    ::

        pip install git+https://github.com/freelawproject/{{NEW-PROJECT}}.git@master



Future
=======

1) Continue to improve ...
2) Future updates

Deployment
==========

If you wish to create a new version manually, the process is:

1. Update version info in ``setup.py``

2. Install the requirements in requirements_dev.txt

3. Set up a config file at ~/.pypirc

4. Generate a universal distribution that worksin py2 and py3 (see setup.cfg)

    ::

        python setup.py sdist bdist_wheel

5. Upload the distributions

    ::

        twine upload dist/* -r pypi (or pypitest)



License
=======

This repository is available under the permissive BSD license, making it easy and safe to incorporate in your own libraries.

Pull and feature requests welcome. Online editing in Github is possible (and easy!)
