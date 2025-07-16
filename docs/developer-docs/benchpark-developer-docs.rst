===============================================
Benchpark Design Concepts and Command Workflow
===============================================

This document outlines the important concepts and patterns used consistently in Benchpark code design, along with detailed explanations of key commands and their workflow.

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

Variants are directives that execute specific logic and set configurations for experiments, systems, and packages. Variants are of the form `name=value`, where the `value` is selected from a set of possible values, defined by the given experiment, system, or package.

**How Variants Work:**

* All possible variants are evaluated at the beginning of the ``concretize()`` function
* This function is called by classes that directly inherits the ``Spec`` class (e.g., ``SystemSpec``, ``ExperimentSpec``)
* We get all possible acceptable variants (args/keywords that, when present, lead to specific configurations being set) that are applicable for the required benchmark/experiment.
* These configurations affect the experiments to run, such as adding specific libraries or tools, and their effect is dumped to configuration files (mainly yaml files) so later Spack and Ramble can provide the needed dependencies/libraries requested.

**Determining Acceptable Variants:**

In both ``benchpark system`` and ``benchpark experiment`` commands, you'll find this pattern::

    cls = ....get_obj_class(self.name)

* ``self`` contains all the Specs, in other words the extra arguments passed in the user command, defined for the current context
* ``self.name`` contains the name of the core component spec relative to the current context, examples:
  
  * ``llnl-cluster`` in benchmark system commands running Benchpark on LLNL systems
    
    * At executing benchpark system command (``benchpark system init --dest=.... llnl-cluster cluster=...``), ``self.name`` resolves to ``llnl-cluster`` since it is the core component, as it defines the system we will run our experiments on
  
  * ``saxpy`` when running benchmark experiment command
    
    * At executing benchpark experiment command (``benchpark experiment init --dest=... saxpy``), ``self.name`` resolves to ``saxpy`` as it is the core component that defines the benchmark that will be used
* A valid question could be, why not the ``cluster=ruby`` be used as ``self.name``?

  * Based on my experiments, order of args passed to benchpark does really matters. By default our parser expects key-value pairs to be at the end, and prior is the Spec name.

* We get the parent directory of the Python class path responsible for creating the ``self.name`` object
* ``self.name`` is set when creating the corresponding child object, (``SystemSpec``, ``ExperimentSpec``) where they inherit from ``Spec`` class (the parent class). This is done right before executing ``concretize()``
* We depend on Ramble for resolving this


**Example:**

For the command::

    benchpark system init --dest=test-ruby-system llnl-cluster cluster=ruby

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
   * Clones Ramble and Spack libraries in the home directory (`~/.benchpark`) if they do not exist.

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

   benchpark system init --dest=test-ruby-system llnl-cluster cluster=ruby

**Generated Output:**

* **YAML files:** Define software needed (to be installed by Spack later)
* **YAML files:** Define the LLNL cluster system to be used

**Generated Directory Structure:** ``test-ruby-system/``

* ``variables.yaml``: Contains configurations for job execution (#nodes, #cores, etc.)

2. Experiment Initialization
----------------------------

**Command:**

.. code-block:: bash

   benchpark experiment init --dest=test-amg2023-benchmark amg2023 +openmp

**Generated Directory Structure:** ``test-amg2023-benchmark/``

* ``ramble.yaml``: 
  
  * Defines experiment variables, which ramble uses to set up experiments.
  * Contains required modifiers and packages to be installed

3. Setup Benchpark Workspace
------------------

**Command:**

.. code-block:: bash

   benchpark setup ./test-amg2023-benchmark ./test-ruby-system test-workspace/

**Generated Directory Structure:** ``test-workspace/``

**New Directory Created:** ``test-amg2023-benchmark/test-ruby-system/workspace``

* Based on definitions in ``test-ruby-system`` and ``test-amg2023-benchmark``
* Contains everything as defined before this step
* Clones Ramble and Spack into the Benchpark workspace

4. Environment Setup
--------------------

**Command:**

.. code-block:: bash

   . test-workspace/setup.sh

**Purpose:**

* Runs two simple scripts to set up Ramble and Spack previously installed for next steps

5. Workspace Configuration
--------------------------

**Location:**

.. code-block:: bash

   cd ./test-workspace/test-amg2023-benchmark/test-ruby-system/workspace/

**Command:**

.. code-block:: bash

   ramble --workspace-dir . --disable-progress-bar workspace setup

**What Happens:**

* **Spack Role:** Installs all needed software
* **Ramble Role:** Sets up all experiments/problems defined in the experiment `ramble.yaml`
* **Benchpark Role:** Complete at this point

**Generated Content:**

* New directory ``experiments`` is created for each experiment in the `ramble.yaml`
* Contains script ``execute_experiment`` for the next step
* This is a job script submitted to the scheduler
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

* Submits the ``execute_experiment`` job script generated from the previous step to the scheduler

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
            "name": "Debug benchpark system init",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/bin/benchpark",
            "args": [
              "system",
              "init",
              "--dest=test-ruby-system",
              "llnl-cluster",
              "cluster=ruby"
            ],
            "console": "integratedTerminal"
          },
          {
            "name": "Debug benchpark experiment init",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/bin/benchpark",
            "args": [
              "experiment",
              "init",
              "--dest=test-saxpy-benchmark",
              "saxpy",
              "+openmp",
              "affinity=mpi"
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
