## Description

- [ ] Replace with: A short description of the change, including motivation and context.
- [ ] Replace with: A list of any dependencies.
- [ ] Replace with: Link(s) to relevant [issue(s)](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword)
- [ ] Complete the checklist for a relevant section(s) below
- [ ] Delete sections below that are not relevant to this PR

## Adding/modifying a system (docs: [Adding a System](https://software.llnl.gov/benchpark/add-a-system-config.html))

- [ ] Add/modify `systems/system_name/system.py` file
- [ ] Add/modify `systems/all_hardware_descriptions/hardware_name/hardware_description.yaml` which will appear in the [docs catalogue](https://software.llnl.gov/benchpark/system-list.html)

## Adding/modifying a benchmark (docs: [Adding a Benchmark](https://software.llnl.gov/benchpark/add-a-benchmark.html))

- [ ] If modifying the source code of a benchmark: create, self-assign, and link here a follow up issue with a link to the PR in the benchmark repo.
- [ ] If package.py upstreamed to Spack is insufficient, add/modify `repo/benchmark_name/package.py` plus: create, self-assign, and link here a follow up issue with a link to the PR in the Spack repo.
- [ ] If application.py upstreamed to Ramble is insufficient, add/modify `repo/benchmark_name/application.py` plus: create, self-assign, and link here a follow up issue with a link to the PR in the Ramble repo.
- [ ] Tags in Ramble's `application.py` or in `repo/benchmark_name/application.py` will appear in the [docs catalogue](https://software.llnl.gov/benchpark/benchmark-list.html)
- [ ] Add/modify an `experiments/benchmark_name/experiment.py` to define an experiment

## Adding/modifying core functionality, CI, or documentation:

- [ ] Update docs
- [ ] Update `.github/workflows` and `.gitlab/tests` unit tests (if needed)
