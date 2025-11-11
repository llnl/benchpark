# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import math
from enum import Enum

from ramble.modkit import *


class AllocOpt(Enum):
    # Experiment resource requests
    N_RANKS = 1
    N_NODES = 2
    N_CORES_PER_RANK = 3
    N_THREADS_PER_PROC = 4  # number of OMP threads per rank
    N_RANKS_PER_NODE = 5
    N_GPUS = 6
    N_CORES_PER_NODE = 7
    OMP_NUM_THREADS = 8

    # Descriptions of resources available on systems
    SYS_GPUS_PER_NODE = 100
    SYS_CORES_PER_NODE = 101
    SYS_MEM_PER_NODE_GB = 102

    # Scheduler identification and other high-level instructions
    SCHEDULER = 200
    TIMEOUT = 201  # This is assumed to be in minutes
    MAX_REQUEST = 202
    QUEUE = 203
    BANK = 204
    MAX_NODES = 205

    # Exec customization for inserting arbitrary options and commands,
    # inserted verbatim
    EXTRA_BATCH_OPTS = 300
    EXTRA_CMD_OPTS = 301
    POST_EXEC_CMDS = 302
    PRE_EXEC_CMDS = 303
    GPU_FACTOR = 304

    @staticmethod
    def as_type(enumval, input):
        if enumval in [
            AllocOpt.SCHEDULER,
            AllocOpt.QUEUE,
            AllocOpt.EXTRA_BATCH_OPTS,
            AllocOpt.EXTRA_CMD_OPTS,
            AllocOpt.POST_EXEC_CMDS,
            AllocOpt.PRE_EXEC_CMDS,
            AllocOpt.BANK,
        ]:
            return str(input)
        else:
            return int(input)


class AllocAlias:
    # Key options, if set, are used to set value options. Type inference
    # occurs before that step, so type inference must be applied to aliases
    # too.
    match = {
        AllocOpt.OMP_NUM_THREADS: AllocOpt.N_THREADS_PER_PROC,
    }


SENTINEL_UNDEFINED_VALUE_STR = "placeholder"
SENTINEL_UNDEFINED_VALUE_INT = 2**64 - 1


class AttrDict(dict):
    """Takes variables defined in AllocOpt, and collects them into a single
    object where, for a given attribute v, and an AttrDict instance x, that
    variable is accessible as "x.v" in Python.

    This is intended to be the most succinct form of access, and not require
    dict access (i.e. `[]`) or string quotation, and also provides the
    benefit that if you try to access a variable not defined in AllocOpt,
    there will be an attribute error.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["_attributes"] = set()

    def __getattr__(self, *args, **kwargs):
        return self.__getitem__(*args, **kwargs)

    def __setattr__(self, *args, **kwargs):
        self.__setitem__(*args, **kwargs)

    def __delattr__(self, *args, **kwargs):
        self.__delitem__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key != "_attributes":
            self["_attributes"].add(key)

    def defined(self):
        return list((k, self[k]) for k in self["_attributes"])

    @staticmethod
    def _nullify_placeholders(v):
        # If we see a string variable set to "placeholder" we assume the
        # user wants us to set it.
        placeholder_checks = {
            int: lambda x: x == SENTINEL_UNDEFINED_VALUE_INT,
            str: lambda x: x == SENTINEL_UNDEFINED_VALUE_STR,
        }
        for var, val in v.defined():
            if val is None:
                continue

            for t, remove_fn in placeholder_checks.items():
                try:
                    read_as = t(val)
                    if remove_fn(read_as):
                        v[var] = None
                except ValueError:
                    pass

    @staticmethod
    def from_predefined_variables(expander):
        var_defs = AttrDict._defined_allocation_options(expander)
        v = AttrDict()
        for alloc_opt in AllocOpt:
            setattr(v, alloc_opt.name.lower(), var_defs.get(alloc_opt, None))

        AttrDict._nullify_placeholders(v)
        AttrDict._propagate_aliases(v)
        return v

    @staticmethod
    def _defined_allocation_options(expander):
        """For each possible allocation option, check if it was defined as a
        variable by the user.

        This includes placeholders (those values are not treated differently
        for this step).
        """
        defined = {}
        for alloc_opt in AllocOpt:
            # print(f"<---- Expanding {str(alloc_opt)}")
            expansion_vref = f"{{{alloc_opt.name.lower()}}}"
            var_def = expander.expand_var(expansion_vref)
            # print(f"    = {str(var_def)}")
            if var_def == expansion_vref:
                # If "{x}" expands to literal "{x}", that means it wasn't
                # defined
                continue
            try:
                val = AllocOpt.as_type(alloc_opt, var_def)
            except ValueError:
                continue

            if val is not None:
                defined[alloc_opt] = val

        return defined

    @staticmethod
    def _propagate_aliases(attr_dict):
        # This assumes that placeholder nullification has already taken place
        # (if it runs before, it may erroneously think that there is a
        # duplicated/conflicting setting when the target is in fact just a
        # placeholder value)
        for alt_var, target in AllocAlias.match.items():
            src_name = alt_var.name.lower()
            dst_name = target.name.lower()
            src_val = getattr(attr_dict, src_name, None)
            dst_val = getattr(attr_dict, dst_name, None)

            if src_val is not None:
                if dst_val is not None and dst_val != src_val:
                    # Both the variable and its alias were set, and to
                    # different values. Note this modifier can be run
                    # multiple times so just looking for whether they
                    # are set would falsely trigger an error
                    raise RuntimeError(f"Configs set {src_name} and {dst_name}")
                setattr(attr_dict, dst_name, src_val)


class TimeFormat:
    @staticmethod
    def hhmmss_tuple(minutes):
        hours = int(minutes / 60)
        minutes = minutes % 60
        seconds = 0
        return (hours, minutes, seconds)

    def as_hhmm(minutes):
        return ":".join(str(x).zfill(2) for x in TimeFormat.hhmmss_tuple(minutes)[:2])

    def as_hhmmss(minutes):
        return ":".join(str(x).zfill(2) for x in TimeFormat.hhmmss_tuple(minutes))


def divide_into(dividend, divisor):
    """For x/y, return the quotient and remainder.

    Attempt to identify cases where a rounding error produces a nonzero
    remainder.
    """
    if divisor > dividend:
        raise ValueError("Dividend must be larger than divisor")
    for x in [dividend, divisor]:
        if not isinstance(x, int):
            raise ValueError("Both values must be integers")
    multi_part = dividend / float(divisor)

    quotient = math.floor(multi_part)
    # Python 3.7 has math.remainder
    remainder = multi_part - quotient
    rounding_err_threshold = 1 / float(dividend)
    if remainder < rounding_err_threshold:
        remainder = 0

    return quotient, remainder


class Allocation(BasicModifier):

    name = "allocation"

    tags("infrastructure")

    # Currently there is only one mode. The only behavior supported right
    # now is to attempt to request "enough" resources for a given
    # request (e.g. to make sure we request enough nodes, assuming we
    # know how many CPUs we want)"
    mode("standard", description="Standard execution mode for allocation")
    default_mode("standard")

    def inherit_from_application(self, app):
        super().inherit_from_application(app)

        v = AttrDict.from_predefined_variables(app.expander)

        # Calculate unset values (e.g. determine n_nodes if not set)
        self.determine_allocation(v)

        self.determine_scheduler_instructions(v)

        # Definitions
        for var, val in v.defined():
            # print(f"<--- Define {str(var)} = {str(val)}")
            if not val:
                val = ""
            app.define_variable(var, str(val))

        if v.n_threads_per_proc:
            self.env_var_modification(
                "OMP_NUM_THREADS",
                method="set",
                modification="{n_threads_per_proc}",
                mode="standard",
            )

    def determine_allocation(self, v):
        if not v.n_ranks:
            if v.n_ranks_per_node and v.n_nodes:
                v.n_ranks = v.n_nodes * v.n_ranks_per_node
            # TODO: elif n_gpus_per_node and n_nodes
            elif v.n_gpus:
                v.n_ranks = v.n_gpus

        if not v.n_nodes:
            if not any((v.n_ranks, v.n_gpus)):
                raise ValueError("Must specify one of: n_nodes, n_ranks, n_gpus")
            cores_node_request = None
            if v.n_ranks:
                multi_cores_per_rank = v.n_cores_per_rank or v.n_threads_per_proc or 0
                cores_request_per_rank = max(multi_cores_per_rank, 1)
                ranks_per_node = math.floor(
                    v.sys_cores_per_node / cores_request_per_rank
                )
                if ranks_per_node == 0:
                    raise ValueError(
                        "Experiment requests more cores per rank than "
                        "are available on a node"
                    )
                cores_node_request = math.ceil(v.n_ranks / ranks_per_node)
            gpus_node_request = None
            if v.n_gpus:
                if v.sys_gpus_per_node:
                    gpus_node_request = math.ceil(v.n_gpus / float(v.sys_gpus_per_node))
                else:
                    raise ValueError(
                        "Experiment requests GPUs, but sys_gpus_per_node "
                        "is not specified for the system"
                    )
            v.n_nodes = max(cores_node_request or 0, gpus_node_request or 0)

        if not v.n_threads_per_proc:
            v.n_threads_per_proc = 1

        # Final check, make sure the above arithmetic didn't result in an
        # unreasonable allocation request.
        for var, val in v.defined():
            try:
                int(val)
            except (ValueError, TypeError):
                continue

        if v.max_nodes and v.n_nodes > v.max_nodes:
            raise ValueError(
                f"{v.n_nodes} nodes is unsatisfiable for queue '{v.queue}' (max {v.max_nodes})."
            )

    def slurm_instructions(self, v):
        sbatch_opts, srun_opts = Allocation._init_batch_and_cmd_opts(v)

        if v.n_ranks:
            srun_opts.append(f"-n {v.n_ranks}")
        if v.n_gpus:
            srun_opts.append(f"--gpus {v.n_gpus}")
        if v.n_nodes:
            srun_opts.append(f"-N {v.n_nodes}")

        if v.queue:
            sbatch_opts.append(f"-p {v.queue}")

        if v.timeout:
            sbatch_opts.append(f"--time {v.timeout}")

        if v.bank:
            sbatch_opts.append(f"--account {v.bank}")

        sbatch_opts.append("--exclusive")

        sbatch_directives = list(f"#SBATCH {x}" for x in (srun_opts + sbatch_opts))

        v.mpi_command = f"srun {' '.join(srun_opts)}"
        v.batch_submit = "sbatch {execute_experiment}"
        v.allocation_directives = "\n".join(sbatch_directives)

    def gpus_as_gpus_per_rank(self, v):
        """Some systems don't have a mechanism for directly requesting a
        total number of GPUs: they just have an option that specifies how
        many GPUs are required for each rank.
        """
        # This error message can come up in multiple scenarios, so pre
        # define it if it's needed (it might not be true except where the
        # error is raised)
        err_msg = (
            f"Cannot express GPUs ({v.n_gpus}) as an integer "
            f"multiple of ranks ({v.n_ranks})"
        )

        if v.n_gpus >= v.n_ranks:
            quotient, remainder = divide_into(v.n_gpus, v.n_ranks)
            if remainder == 0:
                return quotient
            else:
                raise ValueError(err_msg)
        else:
            raise ValueError(err_msg)

    @staticmethod
    def _init_batch_and_cmd_opts(v):
        """System/experiment may have universal options they want to apply
        for all batch allocations or exec calls.
        """
        batch_opts, cmd_opts = [], []
        if v.extra_batch_opts:
            batch_opts.extend(v.extra_batch_opts.strip().split("\n"))
        if v.extra_cmd_opts:
            cmd_opts.extend(v.extra_cmd_opts.strip().split("\n"))

        if v.pre_exec_cmds:
            v.pre_exec = v.pre_exec_cmds
        else:
            v.pre_exec = ""
        if v.post_exec_cmds:
            v.post_exec = v.post_exec_cmds
        else:
            v.post_exec = ""

        return batch_opts, cmd_opts

    def flux_instructions(self, v):
        batch_opts, cmd_opts = Allocation._init_batch_and_cmd_opts(v)

        # Always run exclusive for mpibind + flux.
        # Otherwise, binding may oversubscribe cores before all cores are allocated.
        cmd_opts.append("--exclusive")
        # Required for '--exclusive'. Will be computed, if not defined, from initialization
        cmd_opts.append(f"-N {v.n_nodes}")

        cmd_ranks = ""
        if v.n_ranks:
            cmd_ranks = f"-n {v.n_ranks}"
        if v.n_gpus:
            gpus_per_rank = 1  # self.gpus_as_gpus_per_rank(v)
            cmd_opts.append(f"-g={gpus_per_rank}")

        if v.queue:
            batch_opts.append(f"-q {v.queue}")

        if v.timeout:
            batch_opts.append(f"-t {v.timeout}m")

        if v.bank:
            batch_opts.append(f"-B {v.bank}")

        batch_directives = list(f"# flux: {x}" for x in (cmd_opts + batch_opts))

        v.mpi_command = f"flux run {' '.join([cmd_ranks] + cmd_opts)}"
        v.batch_submit = "flux batch {execute_experiment}"
        v.allocation_directives = "\n".join(batch_directives)

    def mpi_instructions(self, v):
        batch_opts, cmd_opts = Allocation._init_batch_and_cmd_opts(v)
        cmd_opts.extend([f"-n {v.n_ranks}"])

        v.mpi_command = "mpirun " + " ".join(cmd_opts)
        v.batch_submit = "{execute_experiment}"
        v.allocation_directives = ""

    def lsf_instructions(self, v):
        """Note that this generates lrun invocations; lrun  is an LLNL-specific
        tool. jsrun is the generally-available scheduler for IBM Spectrum
        machines (there is not currently a method for generating jsrun
        invocations).
        """
        batch_opts, cmd_opts = Allocation._init_batch_and_cmd_opts(v)

        if v.n_ranks:
            cmd_opts.append(f"-n {v.n_ranks}")
        if v.n_nodes:
            batch_opts.append(f"-nnodes {v.n_nodes}")
        if v.n_gpus:
            gpus_per_rank = self.gpus_as_gpus_per_rank(v)
            cmd_opts.append(f"-g {gpus_per_rank}")
        if v.n_ranks_per_node:
            cmd_opts.append(f"-T {v.n_ranks_per_node}")
        # TODO: this might have to be an option on the batch_submit vs.
        # a batch directive
        if v.queue:
            batch_opts.append(f"-q {v.queue}")
        if v.timeout:
            batch_opts.append(f"-W {TimeFormat.as_hhmm(v.timeout)}")

        batch_directives = list(f"#BSUB {x}" for x in batch_opts)

        v.mpi_command = f"lrun {' '.join(cmd_opts)}"
        v.batch_submit = "bsub {execute_experiment}"
        v.allocation_directives = "\n".join(batch_directives)

    def pjm_instructions(self, v):
        batch_opts, cmd_opts = Allocation._init_batch_and_cmd_opts(v)

        if v.n_ranks:
            batch_opts.append(f"--mpi proc={v.n_ranks}")
        if v.n_nodes:
            batch_opts.append(f'-L "node={v.n_nodes}"')
        if v.timeout:
            batch_opts.append(f'-L "elapse={TimeFormat.as_hhmmss(v.timeout)}"')

        batch_directives = list(f"#PJM {x}" for x in batch_opts)

        v.mpi_command = "mpiexec " + " ".join(cmd_opts)
        v.batch_submit = "pjsub {execute_experiment}"
        v.allocation_directives = "\n".join(batch_directives)

    def determine_scheduler_instructions(self, v):
        handler = {
            "slurm": self.slurm_instructions,
            "flux": self.flux_instructions,
            "mpi": self.mpi_instructions,
            "lsf": self.lsf_instructions,
            "pjm": self.pjm_instructions,
        }
        if v.scheduler not in handler:
            raise ValueError(
                f"scheduler ({v.scheduler}) must be one of : "
                + " ".join(handler.keys())
            )

        handler[v.scheduler](v)
