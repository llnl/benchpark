# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2022-2024 The Ramble Authors
#
# Copyright 2013-2024 Spack Project Developers
#
# SPDX-License-Identifier: Apache-2.0

import collections.abc
import inspect
import os
import re
from typing import Any, Callable, Optional, Tuple, Union

import benchpark.spec
import benchpark.paths
import benchpark.repo
import benchpark.runtime
import benchpark.variant

import ramble.language.language_base
import ramble.language.language_helpers
import ramble.language.shared_language
from ramble.language.language_base import DirectiveError


# TODO remove this when it is added to ramble.lang (when ramble updates from spack)
class classproperty:
    """Non-data descriptor to evaluate a class-level property. The function that performs
    the evaluation is injected at creation time and take an instance (could be None) and
    an owner (i.e. the class that originated the instance)
    """

    def __init__(self, callback):
        self.callback = callback

    def __get__(self, instance, owner):
        return self.callback(owner)


class DirectiveMeta(ramble.language.shared_language.SharedMeta):
    """
    metaclass for supporting directives (e.g., depends_on) and phases
    """

    _directive_names = set()
    _directives_to_be_executed = []

    # Hack to be able to use SharedMeta outside of Ramble
    # will ask Ramble to implement fix on their end and then we can remove this
    def __init__(self, *args, **kwargs):
        with benchpark.repo.override_ramble_hardcoded_globals():
            super(DirectiveMeta, self).__init__(*args, **kwargs)


benchpark_directive = DirectiveMeta.directive


def _make_when_spec(
    value: Optional[Union["benchpark.spec.Spec", str, bool]]
) -> Optional["benchpark.spec.Spec"]:
    """Create a ``Spec`` that indicates when a directive should be applied.

    Directives with ``when`` specs, e.g.:

        patch('foo.patch', when='@4.5.1:')
        depends_on('mpi', when='+mpi')
        depends_on('readline', when=sys.platform() != 'darwin')

    are applied conditionally depending on the value of the ``when``
    keyword argument.  Specifically:

      1. If the ``when`` argument is ``True``, the directive is always applied
      2. If it is ``False``, the directive is never applied
      3. If it is a ``Spec`` string, it is applied when the package's
         concrete spec satisfies the ``when`` spec.

    The first two conditions are useful for the third example case above.
    It allows package authors to include directives that are conditional
    at package definition time, in additional to ones that are evaluated
    as part of concretization.

    Arguments:
        value: a conditional Spec, constant ``bool``, or None if not supplied
           value indicating when a directive should be applied.

    """
    if isinstance(value, benchpark.spec.Spec):
        return value

    # Unsatisfiable conditions are discarded by the caller, and never
    # added to the package class
    if value is False:
        return None

    # If there is no constraint, the directive should always apply;
    # represent this by returning the unconstrained `Spec()`, which is
    # always satisfied.
    if value is None or value is True:
        return benchpark.spec.Spec()

    # This is conditional on the spec
    return benchpark.spec.Spec(value)


@benchpark_directive("variants")
def variant(
    name: str,
    default: Optional[Any] = None,
    description: str = "",
    values: Optional[Union[collections.abc.Sequence, Callable[[Any], bool]]] = None,
    multi: Optional[bool] = None,
    validator: Optional[Callable[[str, str, Tuple[Any, ...]], None]] = None,
    when: Optional[Union[str, bool]] = None,
    sticky: bool = False,
):
    """Define a variant.

    Can specify a default value as well as a text description.

    Arguments:
        name: Name of the variant
        default: Default value for the variant, if not specified otherwise the default will be
            False for a boolean variant and 'nothing' for a multi-valued variant
        description: Description of the purpose of the variant
        values: Either a tuple of strings containing the allowed values, or a callable accepting
            one value and returning True if it is valid
        multi: If False only one value per spec is allowed for this variant
        validator: Optional group validator to enforce additional logic. It receives the experiment
            name, the variant name and a tuple of values and should raise an instance of BenchparkError
            if the group doesn't meet the additional constraints
        when: Optional condition on which the variant applies
        sticky: The variant should not be changed by the concretizer to find a valid concrete spec

    Raises:
        DirectiveError: If arguments passed to the directive are invalid
    """
    if sticky:
        raise NotImplementedError("Sticky variants are not yet implemented in Ramble")

    def format_error(msg, pkg):
        msg += " @*r{{[{0}, variant '{1}']}}"
        return msg.format(pkg.name, name)

    def _always_true(_x):
        return True

    # Ensure we have a sequence of allowed variant values, or a
    # predicate for it.
    if values is None:
        if str(default).upper() in ("TRUE", "FALSE"):
            values = (True, False)
        else:
            values = _always_true

    # The object defining variant values might supply its own defaults for
    # all the other arguments. Ensure we have no conflicting definitions
    # in place.
    for argument in ("default", "multi", "validator"):
        # TODO: we can consider treating 'default' differently from other
        # TODO: attributes and let a packager decide whether to use the fluent
        # TODO: interface or the directive argument
        if hasattr(values, argument) and locals()[argument] is not None:

            def _raise_argument_error(pkg):
                msg = (
                    "Remove specification of {0} argument: it is handled "
                    "by an attribute of the 'values' argument"
                )
                raise DirectiveError(format_error(msg.format(argument), pkg))

            return _raise_argument_error

    # Allow for the object defining the allowed values to supply its own
    # default value and group validator, say if it supports multiple values.
    default = getattr(values, "default", default)
    validator = getattr(values, "validator", validator)
    multi = getattr(values, "multi", bool(multi))

    # Here we sanitize against a default value being either None
    # or the empty string, as the former indicates that a default
    # was not set while the latter will make the variant unparsable
    # from the command line
    if default is None or default == "":

        def _raise_default_not_set(pkg):
            if default is None:
                msg = "either a default was not explicitly set, or 'None' was used"
            elif default == "":
                msg = "the default cannot be an empty string"
            raise DirectiveError(format_error(msg, pkg))

        return _raise_default_not_set

    description = str(description).strip()

    def _execute_variant(pkg):
        when_spec = _make_when_spec(when)

        if not re.match(benchpark.spec.IDENTIFIER, name):
            directive = "variant"
            msg = "Invalid variant name in {0}: '{1}'"
            raise DirectiveError(directive, msg.format(pkg.name, name))

        variants_by_name = pkg.variants.setdefault(when_spec, {})
        variants_by_name[name] = benchpark.variant.Variant(
            name, default, description, values, multi, validator, sticky
        )

    return _execute_variant


class ExperimentSystemBase(metaclass=DirectiveMeta):
    @classproperty
    def template_dir(cls):
        """Directory where the experiment/system.py file lives."""
        return os.path.abspath(os.path.dirname(cls.module.__file__))

    @classproperty
    def module(cls):
        """Module object (not just the name) that this Experiment/System is
        defined in.
        """
        return __import__(cls.__module__, fromlist=[cls.__name__])

    @classproperty
    def namespace(cls):
        """namespace for the Experiment/System, which identifies its repo."""
        parts = cls.__module__.split(".")
        return ".".join(parts[2:-1])

    @classproperty
    def fullname(cls):
        """Name of this Experiment/System, including the namespace"""
        return f"{cls.namespace}.{cls.name}"

    @classproperty
    def fullnames(cls):
        """Fullnames for this Experiment/System and any from which it inherits."""
        fullnames = []
        for cls in inspect.getmro(cls):
            namespace = getattr(cls, "namespace", None)
            if namespace:
                fullnames.append(f"{namespace}.{cls.name}")
            if namespace == "builtin":
                # builtin packages cannot inherit from other repos
                break
        return fullnames

    @classproperty
    def name(cls):
        """The name of this Experiment/System.
        This is the name of its Python module, without the containing module
        names.
        """
        if cls._name is None:
            cls._name = cls.module.__name__
            if "." in cls._name:
                cls._name = cls._name[cls._name.rindex(".") + 1 :]
        return cls._name
