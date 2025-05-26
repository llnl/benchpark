# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import pytest

from benchpark.spec import (
    Spec,
    SpecParser,
    SpecTokenizationError,
    Token,
    TokenType,
)


def simple_spec_name(name):
    """A simple spec name in canonical form"""
    return name, [Token(TokenType.UNQUALIFIED_SPEC_NAME, value=name)], name


@pytest.mark.parametrize(
    "spec_str,tokens,expected_roundtrip",
    [
        # Names names
        simple_spec_name("mvapich"),
        simple_spec_name("mvapich_foo"),
        simple_spec_name("_mvapich_foo"),
        simple_spec_name("3dtk"),
        simple_spec_name("ns-3-dev"),
        # Single token anonymous specs
        ("+foo", [Token(TokenType.BOOL_VARIANT, value="+foo")], "+foo"),
        ("~foo", [Token(TokenType.BOOL_VARIANT, value="~foo")], "~foo"),
        ("-foo", [Token(TokenType.BOOL_VARIANT, value="-foo")], "~foo"),
        (
            "platform=test",
            [Token(TokenType.KEY_VALUE_PAIR, value="platform=test")],
            "platform=test",
        ),
        # Multiple tokens specs
        (
            r"y~f+e~d+c~b+a",  # Variants are reordered
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="y"),
                Token(TokenType.BOOL_VARIANT, value="~f"),
                Token(TokenType.BOOL_VARIANT, value="+e"),
                Token(TokenType.BOOL_VARIANT, value="~d"),
                Token(TokenType.BOOL_VARIANT, value="+c"),
                Token(TokenType.BOOL_VARIANT, value="~b"),
                Token(TokenType.BOOL_VARIANT, value="+a"),
            ],
            "y+a~b+c~d+e~f",
        ),
        (
            r"os=fe",
            [Token(TokenType.KEY_VALUE_PAIR, value="os=fe")],
            "os=fe",
        ),
        # Ambiguous variant specification
        (
            r"_openmpi +debug-qt_4",  # Parse as a single bool variant
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="_openmpi"),
                Token(TokenType.BOOL_VARIANT, value="+debug-qt_4"),
            ],
            r"_openmpi+debug-qt_4",
        ),
        (
            r"_openmpi +debug -qt_4",  # Parse as two variants
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="_openmpi"),
                Token(TokenType.BOOL_VARIANT, value="+debug"),
                Token(TokenType.BOOL_VARIANT, value="-qt_4"),
            ],
            r"_openmpi+debug~qt_4",
        ),
        (
            r"_openmpi +debug~qt_4",  # Parse as two variants
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="_openmpi"),
                Token(TokenType.BOOL_VARIANT, value="+debug"),
                Token(TokenType.BOOL_VARIANT, value="~qt_4"),
            ],
            r"_openmpi+debug~qt_4",
        ),
        # One liner for values like 'a=b=c' that are injected
        (
            "cflags=a=b=c",
            [Token(TokenType.KEY_VALUE_PAIR, value="cflags=a=b=c")],
            "cflags='a=b=c'",
        ),
        (
            "cflags=a=b=c+~",
            [Token(TokenType.KEY_VALUE_PAIR, value="cflags=a=b=c+~")],
            "cflags='a=b=c+~'",
        ),
        (
            "cflags=-Wl,a,b,c",
            [Token(TokenType.KEY_VALUE_PAIR, value="cflags=-Wl,a,b,c")],
            "cflags=-Wl,a,b,c",
        ),
        # Multi quoted
        (
            'cflags="-O3 -g"',
            [Token(TokenType.KEY_VALUE_PAIR, value='cflags="-O3 -g"')],
            "cflags='-O3 -g'",
        ),
    ],
)
def test_parse_single_spec(spec_str, tokens, expected_roundtrip):
    parser = SpecParser(Spec, spec_str)
    assert tokens == parser.tokens()
    assert expected_roundtrip == str(parser.next_spec())


@pytest.mark.parametrize(
    "text,tokens,expected_specs",
    [
        (
            "mvapich emacs",
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="mvapich"),
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="emacs"),
            ],
            ["mvapich", "emacs"],
        ),
        (
            "mvapich cppflags='-O3 -fPIC' emacs",
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="mvapich"),
                Token(TokenType.KEY_VALUE_PAIR, value="cppflags='-O3 -fPIC'"),
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="emacs"),
            ],
            ["mvapich cppflags='-O3 -fPIC'", "emacs"],
        ),
        (
            "mvapich cppflags=-O3 emacs",
            [
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="mvapich"),
                Token(TokenType.KEY_VALUE_PAIR, value="cppflags=-O3"),
                Token(TokenType.UNQUALIFIED_SPEC_NAME, value="emacs"),
            ],
            ["mvapich cppflags=-O3", "emacs"],
        ),
    ],
)
def test_parse_multiple_specs(text, tokens, expected_specs):
    total_parser = SpecParser(Spec, text)
    assert total_parser.tokens() == tokens

    for single_spec_text in expected_specs:
        single_spec_parser = SpecParser(Spec, single_spec_text)
        assert str(total_parser.next_spec()) == str(single_spec_parser.next_spec())


@pytest.mark.parametrize(
    "args,expected",
    [
        # Test that CLI-quoted flags/variant values are preserved
        (["zlib", "cflags=-O3 -g", "+bar", "baz"], "zlib+bar cflags='-O3 -g' baz"),
        # Test that CLI-quoted propagated flags/variant values are preserved
        (["zlib", "cflags==-O3 -g", "+bar", "baz"], "zlib+bar cflags='=-O3 -g' baz"),
        # An entire string passed on the CLI with embedded quotes also works
        (["zlib cflags='-O3 -g' +bar baz"], "zlib+bar cflags='-O3 -g' baz"),
        # Entire string *without* quoted flags splits -O3/-g (-g interpreted as a variant)
        (["zlib cflags=-O3 -g +bar baz"], "zlib+bar~g cflags=-O3 baz"),
        # If the entirety of "-O3 -g +bar baz" is quoted on the CLI, it's all taken as flags
        (["zlib", "cflags=-O3 -g +bar baz"], "zlib cflags='-O3 -g +bar baz'"),
        # If the string doesn't start with key=, it needs internal quotes for flags
        (["zlib", " cflags=-O3 -g +bar baz"], "zlib+bar~g cflags=-O3 baz"),
        # Internal quotes for quoted CLI args are considered part of *one* arg
        (["zlib", 'cflags="-O3 -g" +bar baz'], """zlib cflags='"-O3 -g" +bar baz'"""),
        # Use double quotes if internal single quotes are present
        (["zlib", "cflags='-O3 -g' +bar baz"], '''zlib cflags="'-O3 -g' +bar baz"'''),
        # Use single quotes and escape single quotes with internal single and double quotes
        (
            ["zlib", "cflags='-O3 -g' \"+bar baz\""],
            'zlib cflags="\'-O3 -g\' \\"+bar baz\\""',
        ),
        # Ensure that empty strings are handled correctly on CLI
        (["zlib", "ldflags=", "+pic"], "zlib+pic ldflags=''"),
        # These flags are assumed to be quoted by the shell, so the space
        # becomes part of the value
        (["zlib", "ldflags= +pic"], "zlib ldflags=' +pic'"),
        (["ldflags= +pic"], "ldflags=' +pic'"),
        # If the name is not a flag name, the space is preserved verbatim, because variant values
        # are comma-separated.
        (["zlib", "foo= +pic"], "zlib foo=' +pic'"),
        (["foo= +pic"], "foo=' +pic'"),
        # You can ensure no quotes are added parse_specs() by starting your string with space,
        # but you still need to quote empty strings properly.
        ([" ldflags= +pic"], SpecTokenizationError),
        ([" ldflags=", "+pic"], SpecTokenizationError),
        ([" ldflags='' +pic"], "+pic ldflags=''"),
        ([" ldflags=''", "+pic"], "+pic ldflags=''"),
        # Ensure that empty strings are handled properly in quoted strings
        (["zlib ldflags='' +pic"], "zlib+pic ldflags=''"),
        # Ensure that $ORIGIN is handled correctly
        (
            ["zlib", "ldflags=-Wl,-rpath=$ORIGIN/_libs"],
            "zlib ldflags='-Wl,-rpath=$ORIGIN/_libs'",
        ),
        # Ensure that passing escaped quotes on the CLI raises a tokenization error
        (["zlib", '"-g', '-O2"'], SpecTokenizationError),
    ],
)
def test_cli_spec_roundtrip(args, expected):
    if isinstance(expected, type) and issubclass(expected, BaseException):
        with pytest.raises(expected):
            _ = SpecParser(Spec, args).all_specs()
        return

    specs = SpecParser(Spec, args).all_specs()
    output_string = " ".join(str(spec) for spec in specs)
    for spec in specs:
        print("FINAL", spec)
    print(output_string)
    print(expected)
    assert output_string == expected


@pytest.mark.parametrize(
    "text,expected_in_error",
    [
        ("cflags=''-Wl,a,b,c''", r"cflags=''-Wl,a,b,c''\n            ^ ^ ^ ^^"),
    ],
)
def test_error_reporting(text, expected_in_error):
    parser = SpecParser(Spec, text)
    with pytest.raises(SpecTokenizationError) as exc:
        parser.tokens()

    assert expected_in_error in str(exc), parser.tokens()


@pytest.mark.parametrize(
    "text,match_string",
    [
        # Duplicate variants
        ("x+debug+debug", "variant"),
        ("x+debug debug=true", "variant"),
        ("x debug=false debug=true", "variant"),
        ("x debug=false ~debug", "variant"),
    ],
)
def test_error_conditions(text, match_string):
    with pytest.raises(Exception, match=match_string):
        SpecParser(Spec, text).next_spec()
