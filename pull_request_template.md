# Description

Please provide a short summary of the change and tag any issues being fixed. Please also include relevant motivation
and context. List any dependencies that may be required for this change.

Fixes #<issue>

## Type of Change

- [ ] Adding a system, benchmark, or experiment
- [ ] Modifying an existing system, benchmark, or experiment
- [ ] Documentation update
- [ ] Build/CI update

# Checklist:

If adding/modifying a system:
- [ ] Create a new directory for the system and a new `system.py` file
- [ ] Add a new dry run unit test in `.github/workflows`
- [ ] System appears in System Specifications table in docs catalogue section

If adding/modifying a benchpark:
- [ ] Add a new `application.py` and (maybe) `package.py` under a new directory
      for this benchmark
- [ ] Configure an experiment
- [ ] Benchmark appears in Benchmarks and Experiments table in docs catalogue
      section

If adding/modifying a experiment:
- [ ] Extend `experiment.py` under existing directory for specific benchmark
- [ ] Define a single node and multi-node experiments
