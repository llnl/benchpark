..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#################
 Getting Started
#################

**************
 Installation
**************

Git is needed to clone Benchpark, and Python 3.8+ is needed to run Benchpark:

::

    git clone https://github.com/LLNL/benchpark.git

To add the executable to your path, source the setup script:

::

    cd benchpark
    . setup-env.sh

Now, to check the version you can run:

::

    benchpark --version

**********************
 System Prerequisites
**********************

Once Benchpark is available on your system, its Python dependencies can be installed
using the ``requirements.txt`` file included in the root directory of Benchpark.

To install this, you can use:

::

    python3 -m pip install -r requirements.txt
    benchpark bootstrap

Bootstrap clones the configured Ramble and Spack versions and installs Ramble's Python
requirements from its checkout into the Python environment running Benchpark. Use a
virtual environment if your system Python does not allow package installation. Ordinary
Benchpark commands also bootstrap automatically, installing requirements only when the
active environment is missing a required package or compatible version.

Now you are ready to look at the benchmarks and systems available in Benchpark, and
determine your workflow as described in :doc:`benchpark-commands`.
