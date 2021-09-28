
.. NOTES FOR CREATING A RELEASE:
..
..   * bump the version number in scrubadub_stanford/__init__.py
..   * update docs/changelog.rst
..   * git push
..   * create a release https://github.com/LeapBeyond/scrubadub_stanford/releases
..      * This should trigger a github action to upload to pypi
..      * ReadTheDocs.io should see any changes and also rebuild the docs


******************
scrubadub_stanford
******************

`scrubadub` removes personally identifiable information from text.
`scrubadub_stanford` is an extension that uses Stanford's NER model to remove personal information from text.

This package contains one extra detectors:
 * **StanfordEntityDetector** - A detector that uses the Stanford NER model to find locations, names and organizations.

For more information on how to use this package see the
`scrubadub spacy documentation <https://scrubadub.readthedocs.io/en/develop/names.html#stanford>`_
and the `scrubadub repository <https://github.com/LeapBeyond/scrubadub>`_.


.. image:: https://img.shields.io/github/workflow/status/LeapBeyond/scrubadub_stanford/Python%20package/master
   :target: https://github.com/LeapBeyond/scrubadub_stanford/actions?query=workflow%3A%22Python+package%22+branch%3Amaster
   :alt:  Build Status
.. image:: https://img.shields.io/pypi/v/scrubadub_stanford.svg
   :target: https://pypi.org/project/scrubadub_stanford/
   :alt:  Version
.. image:: https://img.shields.io/pypi/dm/scrubadub_stanford.svg
   :target: https://pypi.org/project/scrubadub_stanford/
   :alt:  Downloads
.. image:: https://coveralls.io/repos/github/LeapBeyond/scrubadub_stanford/badge.svg?branch=master
   :target: https://coveralls.io/r/LeapBeyond/scrubadub_stanford
   :alt:  Test Coverage
.. image:: https://readthedocs.org/projects/scrubadub/badge/?version=latest
   :target: https://readthedocs.org/projects/scrubadub/?badge=latest
   :alt:  Documentation Status


New maintainers
---------------

`LeapBeyond <http://leapbeyond.ai/>`_ are excited to be supporting scrubadub with ongoing maintenance and development.
Thanks to all of the contributors who made this package a success, but especially `@deanmalmgren <https://github.com/deanmalmgren>`_, `IDEO <https://www.ideo.com/>`_ and `Datascope <https://datascopeanalytics.com/>`_.
