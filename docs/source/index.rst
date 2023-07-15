.. Mash documentation master file, created by
   sphinx-quickstart

Overview
========

.. file:///Users/mark/src/python/mash/docs/build/html/modules/filesystem.html

.. sidebar::

    See also:
    `github <https://github.com/voschezang/mash>`_
    |
    `pypi <https://pypi.org/project/mash-shell/>`_

    Usage:
    `Mash Language Reference <https://github.com/voschezang/mash/blob/main/SHELL_REFERENCE.md>`_


.. toctree::
   :caption: Usage:
   :maxdepth: 1

   README <README.md>
   Implementation <SHELL.md>
   Reference <SHELL_REFERENCE.md>


Library Reference
-----------------

.. toctree::
   :caption: Reference:
   :maxdepth: 1

   reference.rst

Internal Packages
~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1
   :caption: Packages:

   filesystem <modules/filesystem>
   object parser <modules/object_parser>
   shell <modules/shell>
   server <modules/server>


Main Classes (Summary)
----------------------


Filesystem
~~~~~~~~~~

* :py:meth:`mash.filesystem.FileSystem`
* :py:meth:`mash.filesystem.Discoverable`
* :py:meth:`mash.filesystem.Option`
* :py:meth:`mash.filesystem.OPTIONS`
* :py:meth:`mash.filesystem.view.View`

Object Parser
~~~~~~~~~~~~~

* :py:meth:`mash.object_parser.build`
    * :py:meth:`mash.object_parser.BuildError`
    * :py:meth:`mash.object_parser.BuildErrors`
    * :py:meth:`mash.object_parser.ErrorMessages`
* :py:meth:`mash.object_parser.OAS`

Shell
~~~~~

* :py:meth:`mash.shell.ShellWithFileSystem`
    * :py:meth:`mash.shell.Shell`
        * :py:meth:`mash.shell.base.BaseShell`
* :py:meth:`mash.shell.errors.ShellError`
* :py:meth:`mash.shell.errors.ShellSyntaxError`


Main Classes (Expanded)
-----------------------

.. autoclass:: mash.filesystem.FileSystem
   :members:
.. autoclass:: mash.filesystem.Discoverable
   :members:
.. autoclass:: mash.filesystem.view.View
   :members:
.. autoclass:: mash.filesystem.Option
   :members:
.. autodata:: mash.filesystem.OPTIONS

.. autofunction:: mash.object_parser.build
.. autoclass:: mash.object_parser.BuildError
   :members:
.. autoclass:: mash.object_parser.BuildErrors
   :members:
.. autoclass:: mash.object_parser.ErrorMessages
   :members:
.. autoclass:: mash.object_parser.OAS
   :members:

.. autoclass:: mash.shell.ShellWithFileSystem
   :members:
.. autoclass:: mash.shell.Shell
   :members:
.. autoclass:: mash.shell.base.BaseShell
   :members:
.. autoclass:: mash.shell.ShellError
   :members:
.. autoclass:: mash.shell.ShellSyntaxError
   :members:

Indices and tables
------------------


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

