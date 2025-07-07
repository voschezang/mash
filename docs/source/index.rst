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

      **Mash Language**

      Using the REPL, browsing directories.

      .. toctree::
         :caption: Mash Language:
         :maxdepth: 3
         :hidden:

         Language Reference <pages/language_reference.md>
         Using directories <pages/directories.md>
         Example scripts <pages/lib.rst>
         Shell CLI <pages/shell_help.rst>

      - `Full language reference <pages/language_reference.html>`_
      - `[How to] Use directories <pages/directories.html>`_
      - `Example scripts <pages/lib.html>`_
      - `Shell CLI <pages/shell_help.html>`_

   .. container:: col

      **Python Source Code**

      Developing a DSL, building the project, extending the language.

      .. toctree::
         :caption: Source Code:
         :maxdepth: 1

         Example scripts <modules/mash_examples.md>

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

      - `Library Reference <pages/reference.html>`_

      .. toctree::
         :hidden:
         :maxdepth: 1
         :caption: Packages:

         filesystem <modules/filesystem>
         object parser <modules/object_parser>
         shell <modules/shell>
         server <modules/server>
         webtools <modules/webtools>

      - Packages
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

