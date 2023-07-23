.. _shell-classes:

Shell
=================

The :code:`Shell` class is based on the builtin module `cmd.Cmd <https://docs.python.org/3/library/cmd.html>`_. 
It extends it with a custom grammer, user-definable variables, functions, pipes and more. There are a few subclasses with specific purposes.

Subclass hierarchy:

.. code-block:: bash

    cmd.Cmd # Python's builtin framework for CLI tools
    └── Cmd2 # Override methods from Cmd. Add error handling and I/O methods.
        └── BaseShell # Support environment variables and sessions
            └── Shell # Use a language model: shell.ast

See `Shell implementation <shell.html>`_.

Core classes
~~~~~~~~~~~~

.. autoclass:: mash.shell.base.Cmd2
   :noindex:
.. autoclass:: mash.shell.base.BaseShell
   :noindex:
.. autoclass:: mash.shell.Shell
   :noindex:
.. autoclass:: mash.shell.ShellWithFileSystem
   :noindex:
