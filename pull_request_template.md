## Description

FIXME:Provide a short summary of the change. Please also include relevant
motivation and context.

Dependencies: FIXME:Add a list of any dependencies.

Fixes issue(s): FIXME:Add list of relevant issues.

## Type of Change

- { } Adding a system, benchmark, or experiment
- { } Modifying an existing system, benchmark, or experiment
- { } Documentation update
- { } Build/CI update
- { } Benchpark core functionality

## Checklist:

If adding/modifying a system:
- { } Create a new directory for the system and a new `system.py` file
- { } Add a new dry run unit test in `.github/workflows`
- { } System appears in System Specifications table in docs catalogue section

If adding/modifying a benchpark:
- { } Add a new `application.py` and (maybe) `package.py` under a new directory
      for this benchmark
- { } Configure an experiment
- { } Benchmark appears in Benchmarks and Experiments table in docs catalogue
      section

If adding/modifying a experiment:
- { } Extend `experiment.py` under existing directory for specific benchmark
- { } Define a single node and multi-node experiments

If adding/modifying core functionality:
- { } Update docs
- { } Update `.github/workflows` and `.gitlab/ci` unit tests (if needed)
