.. _sec-command-line-options:

======================
 Command Line Options
======================

As well as setting options in the `project file <sec-project-options>`, you can
set or override all of them on the command line. This is useful for integrating
Ford into a build system for setting preprocessor defines, include paths, or
the version number, for example.

.. versionadded:: 7.0
   The ``--config`` flag can be used to set *any* option. It takes a
   TOML-formatted, semi-colon separated string, for example:

   .. code:: console

      ford example-project-file.md --config="search=false; parallel=4"

.. sphinx_argparse_cli::
   :module: ford
   :func: get_command_line_arguments
   :hook:
   :no_default_values:
   :prog: ford
   :usage_width: 80
