# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0
import sys
from ramble.appkit import *

class Benchpark(ExecutableApplication):
  """Define a base benchpark application."""

  name = "benchpark"

  register_validator(
    "n_resources_defined",
    predicate="'{n_resources}' != '\{n_resources\}'",
    message="Benchpark requires a definition for 'n_resources', which is how many processes (CPU cores or GPUs) are required",
  )

  register_validator(
	  "process_problem_size_defined",
	  predicate="'{process_problem_size}' != '\{process_problem_size\}'",
	  message="Benchpark requires a definition for 'process_problem_size'",
  )

  register_validator(
	  "total_problem_size_defined",
	  predicate="'{total_problem_size}' != '\{total_problem_size\}'",
	  message="Benchpark requires a definition for 'total_problem_size'",
  )
