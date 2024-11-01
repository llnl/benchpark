.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==============================
Getting Started
==============================

------------
Installation
------------

Git is needed to clone Benchpark, and Python 3.8+ is needed to run Benchpark::

    git clone https://github.com/LLNL/benchpark.git

To add the executable to your path, source the setup script::

    cd benchpark
    . setup-env.sh
    

Now, to check the version you can run:: 

    benchpark --version

--------------------
System Prerequisites
--------------------

Once Benchpark is available on your system, its python dependencies can be
installed using the ``requirements.txt`` file included in the root directory of
Benchpark.

To install this, you can use::

    pip install -r requirements.txt

Now you are ready to look at the benchmarks and systems available in Benchpark, 
and determine your workflow as described in :doc:`basic-usage`.
