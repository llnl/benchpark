# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2024 Spack project developers
#
# SPDX-License-Identifier: Apache-2.0
import inspect


class Variant:
    """Represents a variant in a package, as declared in the
    variant directive.
    """

    def __init__(
        self,
        name,
        default,
        description,
        values=(True, False),
        multi=False,
        validator=None,
        sticky=False,
    ):
        """Initialize a package variant.

        Parameters:
            name (str): name of the variant
            default (str): default value for the variant in case
                nothing has been specified
            description (str): purpose of the variant
            values (sequence): sequence of allowed values or a callable
                accepting a single value as argument and returning True if the
                value is good, False otherwise
            multi (bool): whether multiple CSV are allowed
            validator (callable): optional callable used to enforce
                additional logic on the set of values being validated
            sticky (bool): if true the variant is set to the default value at
                concretization time
        """
        self.name = name
        self.default = default
        self.description = str(description)

        self.values = None
        if values == "*":
            # wildcard is a special case to make it easy to say any value is ok
            self.validator = lambda x: True

        elif isinstance(values, type):
            # supplying a type means any value *of that type*
            def isa_type(v):
                try:
                    values(v)
                    return True
                except ValueError:
                    return False

            self.validator = isa_type

        elif callable(values):
            # If 'values' is a callable, assume it is a single value
            # validator and reset the values to be explicit during debug
            self.validator = values
        else:
            # Otherwise, assume values is the set of allowed explicit values
            self.values = tuple(values)
            self.validator = lambda x: x in self.values

        self.multi = multi
        self.sticky = sticky

    def validate_values(self, variant_values, pkg_cls=None):
        """Validate a variant spec against this package variant. Raises an
        exception if any error is found.

        Parameters:
            vspec_values (tuple): values to be validated
            pkg_cls (spack.package_base.PackageBase): the package class
                that required the validation, if available

        Raises:
            Exception
        """
        # If the value is exclusive there must be at most one
        if not self.multi and len(variant_values) != 1:
            raise Exception()

        # Check and record the values that are not allowed
        not_allowed_values = [
            x for x in variant_values if x != "*" and self.validator(x) is False
        ]
        if not_allowed_values:
            raise ValueError(f"{not_allowed_values} are not valid values for {pkg_cls}")

    def validate_values_bool(self, *args, **kwargs):
        """Wrapper around ``validate_values`` that returns boolean instead of raising."""
        try:
            self.validate_values(*args, **kwargs)
            return True
        except Exception:
            return False

    @property
    def allowed_values(self):
        """Returns a string representation of the allowed values for
        printing purposes

        Returns:
            str: representation of the allowed values
        """
        # Join an explicit set of allowed values
        if self.values is not None:
            v = tuple(str(x) for x in self.values)
            return ", ".join(v)
        # In case we were given a single-value validator
        # print the docstring
        docstring = inspect.getdoc(self.single_value_validator)
        v = docstring if docstring else ""
        return v

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.default == other.default
            and self.values == other.values
            and self.multi == other.multi
            and self.single_value_validator == other.single_value_validator
            and self.group_validator == other.group_validator
        )

    def __ne__(self, other):
        return not self == other
