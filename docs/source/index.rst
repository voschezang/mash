Welcome! This is the documentation for Mash: a *shell* and programming language. It features:


#. A `DSL <https://en.wikipedia.org/wiki/Domain-specific_language>`_ that can interpret user-defined commands.
#. A **REST client** to browse APIs with a programmatic yet intuitive interface.
   
.. raw:: html

   <span>
   See also:
   <a href="https://github.com/voschezang/mash" target="_blank">
      <img src="_static/github-logo.png" alt="GitHub logo"/>
      GitHub
   </a>
   and
   <a href="https://pypi.org/project/mash-shell/" target="_blank">
      <img src="_static/pypi-logo.svg" alt="PyPI logo"/>
      PyPI
   </a>
   <br/> <br/>
   </span>


Documentation
#############

This documentation consists of two sections:

.. container:: two-cols

   .. container:: col

      **1. Mash Language Reference**

      Using the CLI or REPL.

      .. toctree::
         :caption: Mash Language:
         :maxdepth: 3
         :hidden:

         Language Reference <pages/mash/reference.md>
         Symbol Reference <pages/mash/symbols.md>
         Built-in commands <pages/mash/builtins.rst>
         Shell CLI <pages/shell_help.rst>


      - `Full language reference <pages/mash/reference.html>`_
      - `Symbol reference <pages/mash/symbols.html>`_
      - `Built-in commands <pages/mash/builtins.html>`_
      - `Shell CLI <pages/shell_help.html>`_

      Guides and usage examples

      .. toctree::
         :caption: Usage Examples:
         :maxdepth: 3
         :hidden:

         Guides <pages/mash/guides.md>
         Using directories <pages/mash/directories.md>
         Example scripts <pages/lib.rst>

      - `Guides <pages/mash/guides.html>`_
      - `[How to] Use directories <pages/mash/directories.html>`_
      - `Example scripts <pages/lib.html>`_

   .. container:: col

      **Python Source Code**

      Developing a DSL, building the project, extending the language.

      .. toctree::
         :caption: Source Code:
         :maxdepth: 1

         Example scripts <generated/mash_examples.md>

      .. toctree::
         :hidden:

         Shell <pages/shell.md>
         Shell classes <pages/shell_classes.rst>
         Shell AST <pages/ast.rst>

      .. toctree::
         :caption: Reference:
         :maxdepth: 3
         :hidden:

         pages/reference.rst


      .. toctree::
         :hidden:
         :maxdepth: 1
         :caption: Packages:

         filesystem <modules/filesystem>
         object parser <modules/object_parser>
         shell <modules/shell>
         server <modules/server>
         webtools <modules/webtools>


      - `Shell <pages/shell.html>`_
         - `Classes <pages/shell_classes.html>`_
      - `Library Reference <pages/reference.html>`_
         - `Filesystem <modules/filesystem.html>`_
         - `Object parser <modules/object_parser.html#module-object_parser.factory>`_
         - `Shell <pages/shell_classes.html>`_
         - `Shell AST <pages/ast.html>`_
         - `Server <modules/server.html#module-server.server>`_
         - `Webtools <modules/webtools.html#module-webtools>`_


Indices and tables
##################

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

