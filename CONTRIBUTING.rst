Contributor Guide
=================

Thank you for your interest in improving the Home Assistant Custom Component Motion Dimmer.
This project is open-source under the `Apache license`_ and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- `Source Code`_
- `Documentation`_
- `Issue Tracker`_
- `Code of Conduct`_

.. _Apache license: https://opensource.org/license/apache-2-0
.. _Source Code: https://github.com/randomletters/motion_dimmer
.. _Documentation: https://github.com/randomletters/motion_dimmer
.. _Issue Tracker: https://github.com/randomletters/motion_dimmer/issues


How to report a bug
-------------------

Report bugs on the `Issue Tracker`_.

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.


How to request a feature
------------------------

Request features on the `Issue Tracker`_.


How to set up your development environment
------------------------------------------

You need Python and the following tools:

- Docker_
- `Visual Studio Code`_

Fork the repository on GitHub_,
and clone the fork to your local machine. You can now generate a project
from your development version:

.. _Docker: https://www.docker.com/
.. _Visual Studio Code: https://code.visualstudio.com/
.. _Github: https://github.com/randomletters/motion_dimmer


How to test the project
-----------------------

You can run pytest suite manually and you can ensure the integration
generated is working in Home Assistant when launched by Visual Studio
Code in a devcontainer.


How to submit changes
---------------------

Open a `pull request`_ to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- Include unit tests. This project maintains 100% code coverage.
- If your changes add functionality, update the documentation accordingly.

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate your approach.

.. _pull request: https://github.com/randomletters/motion_dimmer/pulls


How to accept changes
---------------------

*You need to be a project maintainer to accept changes.*

Before accepting a pull request, go through the following checklist:

-  The PR must pass all checks.
-  The PR must have a descriptive title.
-  The PR should be labelled with the kind of change (see below).

Release notes are pre-filled with titles and authors of merged pull requests.
Labels group the pull requests into sections.
The following list shows the available sections,
with associated labels in parentheses:

-  💥 Breaking Changes (``breaking``)
-  🚀 Features (``enhancement``)
-  🔥 Removals and Deprecations (``removal``)
-  🐞 Fixes (``bug``)
-  🐎 Performance (``performance``)
-  🚨 Testing (``testing``)
-  👷 Continuous Integration (``ci``)
-  📚 Documentation (``documentation``)
-  🔨 Refactoring (``refactoring``)
-  💄 Style (``style``)
-  📦 Dependencies (``dependencies``)

To merge the pull request, follow these steps:

1. Click **Squash and Merge**.
   (Select this option from the dropdown menu of the merge button, if it is not shown.)
2. Click **Confirm squash and merge**.
3. Click **Delete branch**.


How to make a release
---------------------

*You need to be a project maintainer to make a release.*

Before making a release, go through the following checklist:

-  All pull requests for the release have been merged.
-  The default branch passes all checks.

Releases are made by publishing a GitHub Release.
A draft release is being maintained based on merged pull requests.
To publish the release, follow these steps:

1. Click **Edit** next to the draft release.
2. Enter a tag with the new version.
3. Enter the release title, also the new version.
4. Edit the release description, if required.
5. Click **Publish Release**.

Version numbers adhere to `Calendar Versioning`_,
of the form ``YYYY.MM.Micro``.

After publishing the release, the following automated steps are triggered:

- The Git tag is applied to the repository.

.. _Calendar Versioning: https://calver.org/
.. github-only
.. _Code of Conduct: CODE_OF_CONDUCT.rst
