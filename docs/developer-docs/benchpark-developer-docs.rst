===============================================
Benchpark Design Concepts and Command Workflow
===============================================

This document outlines the important concepts and patterns used consistently in Benchpark (BP) code design, along with detailed explanations of key commands and their workflow.

Table of Contents
=================

This document covers the following main sections:

* `Core Concepts and Patterns`_ - Understanding Variants, Consistent Flow, and Modifiers
* `Benchpark Command Workflow`_ - Step-by-step execution of key Benchpark commands  
* `Debugging Benchpark with VSCode`_ - Setting up debugging environment for development

Core Concepts and Patterns
==========================

1. Variants
-----------

Variants are predefined keywords that execute specific logic and set configurations for benchmarks based on whether these keywords are found in user arguments.

**How Variants Work:**

* All possible variants are evaluated at the beginning of the ``concretize()`` function
* This function is called by classes that directly inherits the ``Spec`` class (e.g., ``SystemSpec``, ``ExperimentSpec``)
* We collect all possible variants (keywords that, when present, lead to specific configurations being set)
* These configurations affect the experiments to run, such as adding specific libraries or tools, and their effect is dumped to configuration files (mainly yaml files) so later Spack and Ramble can procide the needed dependencies/libraries requested.

**Determining Acceptable Variants:**

In both ``benchpark system`` and ``benchpark experiment`` commands, you'll find this pattern::

    cls = ....get_obj_class(self.name)

* ``self`` contains the extra arguments passed in the user command
* ``self.name`` contains the extra arguments passed in the user command
* We get the parent directory of the Python class path responsible for creating the ``self.name`` object
* For example, in ``benchpark system ... command``, this is set when creating the ``SystemSpec`` object that calls its parent class ``Spec``, right before executing ``concretize()``
* We depend on Ramble for resolving this

**Example:**

For the command::

    benchpark system init --dest=amr-ruby-system llnl-cluster cluster=ruby

* ``self.name`` will be resolved to ``llnl-cluster``
* This resolves to get the path of the ``LlnlCluster`` class that contains the variants it accepts

**Variant Processing:**

1. Ramble gets all variants (and dependent variants from any imports of the class) and registers them
2. We check user-provided variants against all acceptable variants to ensure they are as expected
3. Passed user variants are added to generated YAML files
4. Later, we import needed modifiers or load required libraries/tools to provide the requested functionality

2. Consistent Flow for Benchpark Commands
-----------------------------------------

**Flow Overview:**

1. **Entry Point:** ``benchpark`` → ``lib/main.py``
   
   * Gets needed imports, including ``cmd.experiment``
   * Executes ``benchpark.experiment`` (``lib/benchpark/experiment.py``)
   * Checks if Ramble and Spack exist in home directory
   * Clones and installs them if they don't exist

2. **Command Processing:**
   
   * Lists all acceptable commands
   * Parses user command to determine which action to execute (e.g., experiment, system)
   * Executes the corresponding command function:
     
     * ``experiment.py`` → ``command()``
     * ``system.py`` → ``command()``
     * etc.

3. Modifiers
------------

Modifiers provide extra functionality to:

* Help gather more information (such as affinity data)
* Enable tools (such as Caliper) to produce ``.cali`` files for later analysis using Thicket

Benchpark Command Workflow
==========================

1. System Initialization
------------------------

**Command:**

.. code-block:: bash

   benchpark system init --dest=amr-ruby-system llnl-cluster cluster=ruby

**Generated Output:**

* **YAML files:** Define software needed (to be installed by Spack later)
* **YAML files:** Define the LLNL cluster system to be used

**Generated Directory Structure:** ``amr-ruby-system/``

* ``variables.yaml``: Contains configurations for job execution (#nodes, #cores, etc.)

2. Experiment Initialization
----------------------------

**Command:**

.. code-block:: bash

   benchpark experiment init --dest=amg2023-benchmark amg2023 +openmp

**Generated Directory Structure:** ``amg2023-benchmark/``

* ``ramble.yaml``: 
  
  * Defines problems and experiments to run
  * Contains required modifiers and packages to be installed

3. Setup Workspace
------------------

**Command:**

.. code-block:: bash

   benchpark setup ./amr-amg2023-benchmark ./amr-ruby-system amr-workspace/

**Generated Directory Structure:** ``amr-workspace/``

**New Directory Created:** ``amr-amg2023/amr-ruby-system/workspace``

* Based on definitions in ``amr-ruby-system`` and ``amr-amg2023-benchmark``
* Contains everything as defined before this step
* Creates necessary scripts for configuring Ramble and Spack installation

4. Environment Setup
--------------------

**Command:**

.. code-block:: bash

   . amr-workspace/setup.sh

**Purpose:**

* Runs two simple scripts to set up Ramble and Spack previously installed for next steps

5. Workspace Configuration
--------------------------

**Location:**

.. code-block:: bash

   cd ./amr-workspace/amr-amg2023-benchmark/amr-ruby-system/workspace/

**Command:**

.. code-block:: bash

   ramble --workspace-dir . --disable-progress-bar workspace setup

**What Happens:**

* **Spack Role:** Installs all needed software
* **Ramble Role:** Sets up all experiments/problems defined previously for execution
* **Benchpark Role:** Complete at this point

**Generated Content:**

* New directory ``experiments`` is created
* Contains script ``execute_experiment`` for the next step
* This script is the main one that Ramble runs to fire jobs for experiments on the HPC cluster
* Script includes all needed steps to run experiments using:
  
  * Requested benchmark
  * Configurations
  * Packages
  * Libraries
  * etc.

6. Experiment Execution
-----------------------

**Command:**

.. code-block:: bash

   ramble --disable-progress-bar --workspace-dir . on

**Purpose:**

* Runs the ``execute_experiment`` script generated from the previous step
* Execution occurs on the chosen LLNL cluster (e.g., Ruby or Dane)

Debugging Benchpark with VSCode
===============================

This section provides a step-by-step guide for setting up VSCode debugging for Benchpark development.

Setup Instructions
------------------

1. **Install Python Debugger Extension**
   
   Install the official Python debugger extension in VSCode.

2. **Create VSCode Configuration Directory**
   
   In the ``benchpark/`` root directory:
   
   .. code-block:: bash
   
      mkdir .vscode

3. **Create Launch Configuration File**
   
   .. code-block:: bash
   
      touch .vscode/launch.json

4. **Configure Debug Settings**
   
   Paste the following configuration into ``launch.json``:
   
   .. code-block:: json
   
      {
        "version": "0.2.0",
        "configurations": [
          {
            "name": "Debug benchpark init (ruby)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/bin/benchpark",
            "args": [
              "system",
              "init",
              "--dest=amr-ruby-system",
              "llnl-cluster",
              "cluster=ruby"
            ],
            "console": "integratedTerminal"
          },
          {
            "name": "Debug benchpark init (quartz)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/bin/benchpark",
            "args": [
              "system",
              "init",
              "--dest=amr-quartz-system",
              "llnl-cluster",
              "cluster=quartz"
            ],
            "console": "integratedTerminal"
          },
          {
            "name": "Debug benchpark list clusters",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/bin/benchpark",
            "args": [
              "cluster",
              "list"
            ],
            "console": "integratedTerminal"
          }
        ]
      }

5. **Usage Notes**
   
   This configuration provides debugging examples for the commands:
   
   * ``benchpark system init ...``
   * ``benchpark experiment init ...``
   
   Additional commands can be added by appending them to the ``configurations`` array and properly setting the attributes for each new debug configuration.