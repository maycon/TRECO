Installation
============

Prerequisites
-------------

TRECO requires:

* Python 3.14t (free-threaded build)
* `uv <https://github.com/astral-sh/uv>`_ - Fast Python package installer

Why Python 3.14t?
-----------------

Python 3.14t is the **free-threaded** build that removes the Global Interpreter Lock (GIL):

* **True Parallelism**: Multiple threads execute simultaneously without GIL contention
* **Better Timing**: More consistent and precise race window timing
* **Improved Performance**: Better CPU utilization for multi-threaded workloads
* **Perfect for TRECO**: Race condition testing benefits significantly from true parallelism

Installing uv
-------------

If you don't have uv installed:

.. code-block:: bash

   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

Installing Python 3.14t
-----------------------

uv can automatically install Python 3.14t:

.. code-block:: bash

   uv python install 3.14t

Installing TRECO
----------------

From GitHub
~~~~~~~~~~~

.. code-block:: bash

   # Clone repository
   git clone https://github.com/maycon/TRECO.git
   cd TRECO

   # Install with uv
   uv sync

From PyPI (when available)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uv pip install treco

Verifying Installation
----------------------

Check that TRECO is installed correctly:

.. code-block:: bash

   # Activate virtual environment
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows

   # Check version
   treco --version

   # Run help
   treco --help

Development Installation
------------------------

For development work with additional tools:

.. code-block:: bash

   # Clone repository
   git clone https://github.com/maycon/TRECO.git
   cd TRECO

   # Install with development dependencies
   uv sync --all-extras

   # Install pre-commit hooks (optional)
   uv run pre-commit install

Docker Installation
-------------------

You can also run TRECO in Docker:

.. code-block:: bash

   # Build image
   docker build -t treco .

   # Run TRECO
   docker run -v $(pwd)/attacks:/attacks treco attack.yaml

Troubleshooting
---------------

Python Version Issues
~~~~~~~~~~~~~~~~~~~~~

**Problem**: Wrong Python version or GIL not disabled

**Solution**:

.. code-block:: bash

   # Check current Python version
   uv run python --version

   # Should output: Python 3.14.0t (or similar with 't' suffix)

   # List available Python versions
   uv python list

   # Install specific version
   uv python install 3.14t

Permission Errors
~~~~~~~~~~~~~~~~~

**Problem**: Permission denied during installation

**Solution**:

.. code-block:: bash

   # Don't use sudo with uv
   # uv manages its own virtual environments

   # If you see permission errors, check file ownership
   ls -la

Network Issues
~~~~~~~~~~~~~~

**Problem**: Cannot download packages

**Solution**:

.. code-block:: bash

   # Use a different index
   uv pip install --index-url https://pypi.org/simple treco

   # Or configure proxy
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080

Next Steps
----------

* :doc:`quickstart` - Quick start guide
* `GitHub Repository <https://github.com/maycon/TRECO>`_ - Source code and examples
