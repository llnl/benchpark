# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2024 Spack project developers
#
# SPDX-License-Identifier: Apache-2.0

import enum
import io
import json
import pathlib
import re
from typing import Iterable, Iterator, List, Match, Optional, Union

import benchpark.paths
import benchpark.repo
import benchpark.runtime

bootstrapper = benchpark.runtime.RuntimeResources(benchpark.paths.benchpark_home)
bootstrapper.bootstrap()

import llnl.util.lang  # noqa

repo_path = benchpark.repo.paths[benchpark.repo.ObjectTypes.experiments]
sys_repo = benchpark.repo.paths[benchpark.repo.ObjectTypes.systems]


class VariantMap(llnl.util.lang.HashableMap):
    def __init__(self, init: "VariantMap" = None):
        super().__init__()
        if init:
            self.dict = init.dict.copy()

    def __setitem__(self, name: str, values: Union[str, Iterable]):
        if name in self.dict:
            raise Exception(f"Cannot specify variant {name} twice")
        if isinstance(values, str):
            values = (values,)
        else:
            values = tuple(values)
        super().__setitem__(name, values)

    def intersects(self, other: "VariantMap") -> bool:
        if isinstance(other, ConcreteVariantMap):
            return other.intersects(self)

        # always possible to constrain since abstract variants are multi-value
        return True

    def satisfies(self, other: "VariantMap") -> bool:
        if isinstance(other, ConcreteVariantMap):
            self == other

        return all(
            name in self and set(self[name]) >= set(other[name]) for name in other
        )

    def constrain(self, other: "VariantMap") -> None:
        for name in other:
            self_values = list(self.dict.get(name, []))
            values = llnl.util.lang.dedupe(self_values + list(other[name]))
            self[name] = values

    @staticmethod
    def stringify(name: str, values: tuple) -> str:
        if len(values) == 1:
            if values[0].lower() == "true":
                return f"+{name}"
            if values[0].lower() == "false":
                return f"~{name}"
        v_string = quote_if_needed(",".join(values))
        return f"{name}={v_string}"

    def __str__(self):
        if not self:
            return ""

        # print keys in order
        sorted_keys = sorted(self.keys())

        # Separate boolean variants from key-value pairs as they print
        # differently. All booleans go first to avoid ' ~foo' strings that
        # break spec reuse in zsh.
        bool_keys = []
        kv_keys = []
        for key in sorted_keys:
            is_bool = len(self[key]) == 1 and self[key][0].lower() in ("true", "false")
            bool_keys.append(key) if is_bool else kv_keys.append(key)

        # add spaces before and after key/value variants.
        string = io.StringIO()

        string.write("".join(self.stringify(key, self[key]) for key in bool_keys))
        if bool_keys and kv_keys:
            string.write(" ")

        string.write(" ".join(self.stringify(key, self[key]) for key in kv_keys))

        return string.getvalue()


class ConcreteVariantMap(VariantMap):
    def __setitem__(self, name, values):
        raise TypeError(f"{self.__class__} is immutable.")

    def intersects(self, other: VariantMap) -> bool:
        return self.satisfies(other)


class Spec(object):
    def __init__(self, str_or_spec: Optional[Union[str, "Spec"]] = None):
        self._name = None
        self._namespace = None
        self._variants = VariantMap()

        if isinstance(str_or_spec, Spec):
            self._dup(str_or_spec)
        elif isinstance(str_or_spec, str):
            self._parse(str_or_spec)
        elif str_or_spec is not None:
            msg = f"{self.__class__} can only be instantiated from {self.__class__} or str, "
            msg += f"not from {type(str_or_spec)}."
            raise NotImplementedError(msg)

    # getter/setter for each attribute so that ConcreteSpec can be immutable
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value: str):
        self._namespace = value

    @property
    def variants(self):
        return self._variants

    # This one is probably unnecessary, but here for completeness
    @variants.setter
    def variants(self, value: VariantMap):
        self._variants = value

    def __eq__(self, other: "Spec"):
        if other is None:
            return False

        return (
            self.name == other.name
            and (
                self.namespace is None
                or other.namespace is None
                or self.namespace == other.namespace
            )
            and self.variants == other.variants
        )

    def __hash__(self):
        # If hashing specs, client code is responsible for ensuring they do not mutate
        return hash((self.name, self.namespace, self.variants))

    def __str__(self):
        string = ""
        if self.namespace is not None:
            string += f"{self.namespace}."
        if self.name is not None:
            string += self.name

        variants = str(self.variants)
        if string and variants and not variants.startswith(("+", "~")):
            string += " "
        string += variants
        return string

    def __repr__(self):
        return str(self)

    def _dup(self, other: "Spec"):
        # operate on underlying types so it can be called on ConcreteSpec
        self._name = other.name
        self._namespace = other.namespace
        self._variants = other.variants

    def _parse(self, string: str):
        specs = SpecParser(
            type(self), string
        ).all_specs()  # parse spec of appropriate type
        assert len(specs) == 1, f"{string} does not parse to one spec"

        self._dup(specs[0])

    def intersects(self, other: Union[str, "Spec"]) -> bool:
        if not isinstance(other, Spec):
            other = Spec(other)  # subclasses do not override intersects behavior
        return (
            (self.name is None or other.name is None or self.name == other.name)
            and (
                self.namespace is None
                or other.namespace is None
                or self.namespace == other.namespace
            )
            and self.variants.intersects(other.variants)
        )

    def satisfies(self, other: Union[str, "Spec"]) -> bool:
        if not isinstance(other, Spec):
            other = Spec(other)  # subclasses do not override satisfies behavior
        return (
            (other.name is None or self.name == other.name)
            and (other.namespace is None or self.namespace == other.namespace)
            and self.variants.satisfies(other.variants)
        )

    def constrain(self, other: Union[str, "Spec"]) -> None:
        if not isinstance(other, Spec):
            other = Spec(other)
        if other.name:
            if self.name and self.name != other.name:
                raise Exception
            self.name == other.name

        if other.namespace:
            if self.namespace and self.namespace != other.namespace:
                raise Exception
            self.namespace == other.namespace

        self.variants.constrain(other.variants)

    def concretize(self):
        raise NotImplementedError("Spec.concretize must be implemented by subclass")

    @property
    def object_class(self):
        raise NotImplementedError(
            f"{type(self)} does not implement object_class property"
        )


class ExperimentSpec(Spec):
    @property
    def experiment_class(self):
        return repo_path.get_obj_class(self.name)

    @property
    def object_class(self):
        # shared getter so that multiple spec types can be concretized similarly
        return self.experiment_class

    def concretize(self):
        return ConcreteExperimentSpec(self)


class ConcreteSpec(Spec):
    def __init__(self, str_or_spec: Union[str, Spec]):
        super().__init__(str_or_spec)
        self._concretize()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        raise TypeError(f"{self.__class__} is immutable")

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value: str):
        raise TypeError(f"{self.__class__} is immutable")

    @property
    def variants(self):
        return self._variants

    @variants.setter
    def variants(self, value: str):
        raise TypeError(f"{self.__class__} is immutable")

    def _concretize(self):
        if not self.name:
            raise AnonymousSpecError(f"Cannot concretize anonymous {type(self)} {self}")

        if not self.namespace:
            self._namespace = self.object_class.namespace

        # For variants that are set, set whatever they imply
        variants_to_check = set(
            (name, values) for name, values in self.variants.items()
        )
        checked = set()
        while variants_to_check:
            name, values = variants_to_check.pop()
            checked.add((name, values))

            conditions = [
                w
                for w, v_by_n in self.object_class.variants.items()
                for n, v in v_by_n.items()
                if n == name and v.validate_values_bool(values)
            ]

            if not conditions:
                raise Exception(f"{name} is not a valid variant of {self.name}")

            # This variant is already valid on self
            if any(self.satisfies(c) for c in conditions):
                continue

            # If there is not a condition that allows this variant already, add one
            cond = conditions[0]
            for n, v in cond.variants.items():
                if (n, v) not in checked:
                    variants_to_check.add((n, v))
            self.constrain(cond)

        # Concretize variants that aren't set
        changed = True
        while changed:
            changed = False

            for when, variants_by_name in self.object_class.variants.items():
                for name, variant in variants_by_name.items():
                    if self.satisfies(when):
                        if name not in self.variants:
                            changed = True
                            self._variants[name] = variant.default

        # Validate all set variant values
        for name, values in self.variants.items():
            try:
                variant = next(
                    v
                    for w, v_by_n in self.object_class.variants.items()
                    for n, v in v_by_n.items()
                    if self.satisfies(w) and n == name
                )
            except StopIteration:
                raise Exception(f"{name} is not a valid variant of {self.name}")

            variant.validate_values(self.variants[name])

        # Convert to immutable type
        self._variants = ConcreteVariantMap(self.variants)


class ConcreteExperimentSpec(ConcreteSpec, ExperimentSpec):
    @property
    def experiment(self) -> "benchpark.Experiment":
        return self.experiment_class(self)


class SystemSpec(Spec):
    @property
    def system_class(self):
        cls = sys_repo.get_obj_class(self.name)
        # TODO: this shouldn't be necessary, but .template_dir isn't working
        cls.resource_location = pathlib.Path(
            sys_repo.filename_for_object_name(self.name)
        ).parent
        return cls

    @property
    def object_class(self):
        # shared getter so that multiple spec types can be concretized similarly
        return self.system_class

    def concretize(self):
        return ConcreteSystemSpec(self)


class ConcreteSystemSpec(ConcreteSpec, SystemSpec):
    @property
    def system(self) -> "benchpark.System":
        return self.system_class(self)


# PARSING STUFF BELOW HERE

#: Valid name for specs and variants. Here we are not using
#: the previous "w[\w.-]*" since that would match most
#: characters that can be part of a word in any language
IDENTIFIER = r"(?:[a-zA-Z_0-9][a-zA-Z_0-9\-]*)"
DOTTED_IDENTIFIER = rf"(?:{IDENTIFIER}(?:\.{IDENTIFIER})+)"
NAME = r"[a-zA-Z_0-9][a-zA-Z_0-9\-.]*"

#: These are legal values that *can* be parsed bare, without quotes on the command line. Cannot start with `=`
VALUE = r"(?:[a-zA-Z_0-9\-+\*.,:\~\/\\][a-zA-Z_0-9\-+\*.,:=\~\/\\]*)"

#: Variant/flag values that match this can be left unquoted in Spack output
NO_QUOTES_NEEDED = re.compile(r"^[a-zA-Z0-9,/_.-]+$")

#: Quoted values can be *anything* in between quotes, including escaped quotes.
QUOTED_VALUE = r"(?:'(?:[^']|(?<=\\)')*'|\"(?:[^\"]|(?<=\\)\")*\")"

#: Regex with groups to use for splitting (optionally propagated) key-value pairs
SPLIT_KVP = re.compile(rf"^({NAME})=(.*)$")


class TokenBase(enum.Enum):
    """Base class for an enum type with a regex value"""

    def __new__(cls, *args, **kwargs):
        # See
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, regex):
        self.regex = regex

    def __str__(self):
        return f"{self._name_}"


class TokenType(TokenBase):
    """Enumeration of the different token kinds in the spec grammar.

    Order of declaration is extremely important, since text containing specs is parsed with a
    single regex obtained by ``"|".join(...)`` of all the regex in the order of declaration.
    """

    # variants
    BOOL_VARIANT = rf"(?:[~+-]\s*{NAME})"
    KEY_VALUE_PAIR = rf"(?:{NAME}=(?:{VALUE}|{QUOTED_VALUE}))"
    # Package name
    FULLY_QUALIFIED_SPEC_NAME = rf"(?:{DOTTED_IDENTIFIER})"
    UNQUALIFIED_SPEC_NAME = rf"(?:{IDENTIFIER})"
    # White spaces
    WS = r"(?:\s+)"


class ErrorTokenType(TokenBase):
    """Enum with regexes for error analysis"""

    # Unexpected character
    UNEXPECTED = r"(?:.[\s]*)"


#: Regex to strip quotes. Group 2 will be the unquoted string.
STRIP_QUOTES = re.compile(r"^(['\"])(.*)\1$")


def quote_kvp(string: str) -> str:
    """For strings like ``name=value``, quote and escape the value if needed.

    This is a compromise to respect quoting of key-value pairs on the CLI. The shell
    strips quotes from quoted arguments, so we cannot know *exactly* how CLI arguments
    were quoted. To compensate, we re-add quotes around anything staritng with ``name=``,
    and we assume the rest of the argument is the value. This covers the
    common cases of passing variant arguments with spaces in them, e.g.,
    ``cflags="-O2 -g"`` on the command line.
    """
    match = SPLIT_KVP.match(string)
    if not match:
        return string

    key, value = match.groups()
    return f"{key}={quote_if_needed(value)}"


def strip_quotes_and_unescape(string: str) -> str:
    """Remove surrounding single or double quotes from string, if present."""
    match = STRIP_QUOTES.match(string)
    if not match:
        return string

    # replace any escaped quotes with bare quotes
    quote, result = match.groups()
    return result.replace(rf"\{quote}", quote)


def quote_if_needed(value: str) -> str:
    """Add quotes around the value if it requires quotes.

    This will add quotes around the value unless it matches ``NO_QUOTES_NEEDED``.

    This adds:
    * single quotes by default
    * double quotes around any value that contains single quotes

    If double quotes are used, we json-escape the string. That is, we escape ``\\``,
    ``"``, and control codes.

    """
    if NO_QUOTES_NEEDED.match(value):
        return value

    return json.dumps(value) if "'" in value else f"'{value}'"


class Token:
    """Represents tokens; generated from input by lexer and fed to parse()."""

    __slots__ = "kind", "value", "start", "end"

    def __init__(
        self,
        kind: TokenBase,
        value: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        self.kind = kind
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"({self.kind}, {self.value})"

    def __eq__(self, other):
        return (self.kind == other.kind) and (self.value == other.value)


#: List of all the regexes used to match spec parts, in order of precedence
TOKEN_REGEXES = [rf"(?P<{token}>{token.regex})" for token in TokenType]
#: List of all valid regexes followed by error analysis regexes
ERROR_HANDLING_REGEXES = TOKEN_REGEXES + [
    rf"(?P<{token}>{token.regex})" for token in ErrorTokenType
]
#: Regex to scan a valid text
ALL_TOKENS = re.compile("|".join(TOKEN_REGEXES))
#: Regex to analyze an invalid text
ANALYSIS_REGEX = re.compile("|".join(ERROR_HANDLING_REGEXES))


def tokenize(text: str) -> Iterable[Token]:
    """Return a token generator from the text passed as input.

    Raises:
        SpecTokenizationError: if we can't tokenize anymore, but didn't reach the
            end of the input text.
    """
    scanner = ALL_TOKENS.scanner(text)  # type: ignore[attr-defined]
    match: Optional[Match] = None
    for match in iter(scanner.match, None):
        # The following two assertions are to help mypy
        msg = "unexpected value encountered during parsing. Please submit a bug report "
        assert match is not None, msg
        assert match.lastgroup is not None, msg
        yield Token(
            TokenType.__members__[match.lastgroup],
            match.group(),
            match.start(),
            match.end(),
        )

    if match is None and not text:
        # We just got an empty string
        return

    if match is None or match.end() != len(text):
        error_scanner = ANALYSIS_REGEX.scanner(text)
        matches = [m for m in iter(error_scanner.match, None)]
        raise SpecTokenizationError(matches, text)


class TokenContext:
    """Token context passed around by parsers"""

    __slots__ = "token_stream", "current_token", "next_token"

    def __init__(self, token_stream: Iterator[Token]):
        self.token_stream = token_stream
        self.current_token = None
        self.next_token = None
        self.advance()

    def advance(self):
        """Advance one token"""
        self.current_token, self.next_token = self.next_token, next(
            self.token_stream, None
        )

    def accept(self, kind: TokenType):
        """If the next token is of the specified kind, advance the stream and return True.
        Otherwise return False.
        """
        if self.next_token and self.next_token.kind == kind:
            self.advance()
            return True
        return False

    def expect(self, *kinds: TokenType):
        return self.next_token and self.next_token.kind in kinds


class SpecParser(object):
    __slots__ = "literal_str", "ctx", "type"

    def __init__(self, type, literal: Union[str, list]):
        if isinstance(literal, list):
            self.literal_str = " ".join([quote_kvp(arg) for arg in literal])
        else:
            self.literal_str = literal
        self.ctx = TokenContext(
            filter(lambda x: x.kind != TokenType.WS, tokenize(self.literal_str))
        )
        self.type = type

    def tokens(self) -> List[Token]:
        """Return the entire list of token from the initial text. White spaces are
        filtered out.
        """
        return list(
            filter(lambda x: x.kind != TokenType.WS, tokenize(self.literal_str))
        )

    def next_spec(self) -> Optional[Spec]:
        """Return the next spec parsed from text.

        Parameters:
            initial_spec: object where to parse the spec. If None a new one
                will be created.

        Returns:
            The spec that was parsed
        """
        if not self.ctx.next_token:
            return None

        spec = self.type()

        if self.ctx.accept(TokenType.UNQUALIFIED_SPEC_NAME):
            spec.name = self.ctx.current_token.value
        elif self.ctx.accept(TokenType.FULLY_QUALIFIED_SPEC_NAME):
            parts = self.ctx.current_token.value.split(".")
            name = parts[-1]
            namespace = ".".join(parts[:-1])
            spec.name = name
            spec.namespace = namespace

        while True:
            if self.ctx.accept(TokenType.BOOL_VARIANT):
                name = self.ctx.current_token.value[1:].strip()
                value = self.ctx.current_token.value[0] == "+"
                spec.variants[name] = str(value).lower()
            elif self.ctx.accept(TokenType.KEY_VALUE_PAIR):
                match = SPLIT_KVP.match(self.ctx.current_token.value)
                assert (
                    match
                ), f"SPLIT_KVP cannot split pair {self.ctx.current_token.value}"

                name, value = match.groups()
                spec.variants[name] = strip_quotes_and_unescape(value).split(",")
            else:
                break

        return spec

    def all_specs(self) -> List[Spec]:
        return list(iter(self.next_spec, None))


# ERROR HANDLING BELOW HERE


class AnonymousSpecError(Exception):
    pass


class SpecTokenizationError(Exception):
    """Syntax error in a spec string"""

    def __init__(self, matches, text):
        message = "unexpected tokens in the spec string\n"
        message += f"{text}"

        underline = "\n"
        for match in matches:
            if match.lastgroup == str(ErrorTokenType.UNEXPECTED):
                underline += f"{'^' * (match.end() - match.start())}"
                continue
            underline += f"{' ' * (match.end() - match.start())}"

        message += underline
        super().__init__(message)
