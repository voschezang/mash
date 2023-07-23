.. Mash documentation master file, created by
   sphinx-quickstart


Overview
========

.. sidebar::

    See also:
    `github <https://github.com/voschezang/mash>`_
    |
    `pypi <https://pypi.org/project/mash-shell/>`_


    | Mash language usage:

    * `• Reference <https://github.com/voschezang/mash/blob/main/SHELL_REFERENCE.md>`_
    * `• Example script <pages/lib.html>`_


.. toctree::
   :caption: Usage:
   :maxdepth: 1

   README <pages/README.md>
   Implementation <pages/shell.md>
   Shell CLI <pages/shell_help.rst>
   Example code <modules/mash_examples.md>

.. toctree::
   :hidden:

   Reference <pages/SHELL_REFERENCE.md>
   Example Mash script <pages/lib.rst>


Library Reference
-----------------

.. toctree::
   :caption: Reference:
   :maxdepth: 1

   pages/reference.rst
   Shell AST <pages/ast.rst>
   Shell Classes <pages/shell_classes.rst>

Packages

- `Shell <pages/shell.html>`_
- `Filesystem <modules/filesystem.html>`_
- `Object parser <modules/object_parser.html#module-object_parser.factory>`_
- `Server <modules/server.html#module-server.server>`_
- `Webtools <modules/webtools.html#module-webtools>`_


Internal Packages
~~~~~~~~~~~~~~~~~

Packages

.. toctree::
   :maxdepth: 1
   :caption: Packages:

   filesystem <modules/filesystem>
   object parser <modules/object_parser>
   shell <modules/shell>
   server <modules/server>
   webtools <modules/webtools>


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

