## Description

- [ ] Replace with: A short description of the change, including motivation and context.
- [ ] Replace with: A list of any dependencies.
- [ ] Replace with: Link(s) to relevant [issue(s)](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword)
- [ ] Complete the checklist for a relevant section(s) below
- [ ] Delete sections below that are not relevant to this PR

## Adding/modifying a system (docs: [Adding a System](https://software.llnl.gov/benchpark/add-a-system-config.html))

- [ ] Add/modify `systems/system_name/Create a new directory for the system, add/modify `system.py` file
- [ ] Add/modify a dry run unit test in `.github/workflows/run.yml`
- [ ] Add/modify `systems/all_system_definitions/system-hardware/system_definition.yaml which will appear in the [docs catalogue](https://software.llnl.gov/benchpark/system-list.html)

## Adding/modifying a benchmark (docs: [Adding a Benchmark](https://software.llnl.gov/benchpark/add-a-benchmark.html))

- [ ] (optional) If package upstreamed to Spack is insufficient, add/modify `repo/benchmark_name/package.py`
- [ ] (optional) If application upstreamed to Ramble is insufficient, add/modify `repo/benchmark_name/application.py`
- [ ] Tags in Ramble's `application.py` or in `repo/benchmark_name/application.py` will appear in the [docs catalogue](https://software.llnl.gov/benchpark/benchmark-list.html)
- [ ] Add/modify an `experiments/benchmark_name/experiment.py` to define a single node and multi-node experiments
- [ ] Add/modify a dry run unit test in `.github/workflows/run.yml`

## Adding/modifying core functionality, CI, or documentation:

- [ ] Update docs
- [ ] Update `.github/workflows` and `.gitlab/ci` unit tests (if needed)
