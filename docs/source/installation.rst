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

You should see output like:

.. code-block:: text

   Treco v1.0.0

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

Dependencies
------------

TRECO automatically installs these dependencies:

* **requests** (>=2.31.0): HTTP client library
* **pyyaml** (>=6.0.1): YAML parser
* **jinja2** (>=3.1.2): Template engine
* **pyotp** (>=2.9.0): TOTP generation
* **colorama** (>=0.4.6): Colored terminal output
* **jsonpath-ng** (>=1.6.0): JSONPath support
* **lxml**: XPath support for XML/HTML parsing

Docker Installation
-------------------

You can also run TRECO in Docker:

.. code-block:: bash

   # Build image
   docker build -t treco .

   # Run TRECO
   docker run -v $(pwd)/attacks:/attacks treco attack.yaml

Docker Compose
~~~~~~~~~~~~~~

For more complex setups:

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   services:
     treco:
       build: .
       volumes:
         - ./attacks:/attacks
       command: attack.yaml

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

**Problem**: Python 3.14t not available

**Solution**: Make sure uv is up to date:

.. code-block:: bash

   # Update uv
   uv self update

   # Try installing again
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

   # Fix ownership if needed
   sudo chown -R $USER:$USER .

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

lxml Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: lxml fails to install (especially on macOS)

**Solution**:

.. code-block:: bash

   # macOS - install dependencies first
   brew install libxml2 libxslt

   # Ubuntu/Debian
   sudo apt-get install libxml2-dev libxslt-dev

   # Then retry installation
   uv sync

Virtual Environment Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Commands not found after installation

**Solution**:

.. code-block:: bash

   # Make sure you're in the virtual environment
   source .venv/bin/activate

   # Or use uv run
   uv run treco --version

System-Specific Notes
---------------------

Linux
~~~~~

TRECO works best on Linux due to better thread timing precision:

.. code-block:: bash

   # Ubuntu/Debian prerequisites
   sudo apt-get update
   sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

   # Fedora/CentOS prerequisites
   sudo dnf install gcc openssl-devel libffi-devel python3-devel

macOS
~~~~~

On macOS, you may need Xcode command line tools:

.. code-block:: bash

   xcode-select --install

Windows
~~~~~~~

For best results on Windows, use WSL2:

.. code-block:: bash

   # Install WSL2
   wsl --install

   # Then follow Linux installation steps

If using native Windows:

.. code-block:: powershell

   # PowerShell
   uv python install 3.14t
   git clone https://github.com/maycon/TRECO.git
   cd TRECO
   uv sync

Next Steps
----------

* :doc:`quickstart` - Quick start guide
* :doc:`configuration` - YAML configuration reference
* :doc:`examples` - Real-world attack examples
* `GitHub Repository <https://github.com/maycon/TRECO>`_ - Source code and examples
