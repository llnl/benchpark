import argparse

import spack.cmd
import spack.environment as ev
import spack.traverse as traverse
from llnl.util.tty.color import cwrite


def diff_specs(spec_a, spec_b, truncate=False):
    def highlight(element):
        cwrite("@R{%s}" % str(element))

    def _write(s):
        print(s, end="")

    def _variant_str(v):
        if isinstance(v, spack.variant.BoolValuedVariant):
            return str(v)
        else:
            return " " + str(v)

    class VariantsComparator:
        def __init__(self, spec, truncate):
            self.variants = spec.variants
            self.truncate = truncate

        def compare(self, other_spec):
            if not self.variants:
                return
            for k, v in self.variants.items():
                if k not in other_spec.variants:
                    highlight(_variant_str(v))
                elif not v.satisfies(other_spec.variants[k]):
                    highlight(_variant_str(v))
                elif not self.truncate:
                    _write(_variant_str(v))
                # else: there is no difference and truncate=True

    class VersionComparator:
        def __init__(self, spec, truncate):
            self.version = spec.version
            self.truncate = truncate

        def compare(self, other_spec):
            other_version = other_spec.version

            if not self.version.satisfies(other_version):
                highlight(f"@{self.version}")
            elif not self.truncate:
                _write(f"@{self.version}")

    class CompilerComparator:
        def __init__(self, spec, truncate):
            self.compiler = spec.compiler
            self.truncate = truncate

        def compare(self, other_spec):
            other_cmp = other_spec.compiler
            if self.compiler.name != other_cmp.name:
                highlight(f"%{self.compiler}")
            else:
                if not self.compiler.version.satisfies(other_cmp.version):
                    _write(f"%{self.compiler.name}")
                    highlight("@{self.compiler.version}")
                elif not self.truncate:
                    _write(f"%{self.compiler}")

    class DepsComparator:
        def __init__(self, spec, newline_cb):
            self.spec = spec
            self.newline_cb = newline_cb

        def compare(self, other_spec):
            self_deps = set(x.name for x in self.spec.dependencies())
            other_deps = set(x.name for x in other_spec.dependencies())
            extra = list(sorted(self_deps - other_deps))
            if extra:
                self.newline_cb()
                highlight(f"-> [{' '.join(extra)}]")

    class ArchComparator:
        def __init__(self, spec, truncate):
            self.arch = spec.architecture
            self.truncate = truncate

        def _component_wise_diff(self, x, y, separator):
            pairs = list(zip(x, y))
            size = len(pairs)
            for i, (xi, yi) in enumerate(pairs):
                if xi == yi:
                    _write(xi)
                else:
                    highlight(f"{xi}/{yi}")
                # I want to put `separator` "between" components. Since I'm
                # writing as I go, I need to handle this fenceposting issue
                # manually
                if i < size - 1:
                    _write(separator)

        def compare(self, other_spec):
            this = [self.arch.platform, self.arch.os, str(self.arch.target)]
            other_arch = other_spec.architecture
            other = [other_arch.platform, other_arch.os, str(other_arch.target)]
            if this != other:
                _write(" arch=")
                self._component_wise_diff(this, other, "-")
            elif not self.truncate:
                _write(f" arch={self.arch}")

    class NewlineWithDepthIndent:
        def __init__(self):
            self.depth = 0

        def __call__(self):
            print()
            _write("  " * self.depth)

    nl_cb = NewlineWithDepthIndent()

    def decompose(spec):
        return [
            VersionComparator(spec, truncate),
            CompilerComparator(spec, truncate),
            VariantsComparator(spec, truncate),
            ArchComparator(spec, truncate),
            DepsComparator(spec, nl_cb),
        ]

    diff = False
    for depth, dep_spec in traverse.traverse_tree(
        [spec_a], deptype=("link", "run"), depth_first=True
    ):
        indent = "  " * depth
        nl_cb.depth = depth
        node = dep_spec.spec
        _write(indent)
        if node.name in spec_b:
            _write(node.name)

            comparators = decompose(node)
            for c in comparators:
                c.compare(spec_b[node.name])
        else:
            highlight(node.name)
            diff = True
        print()  # New line
    return diff


def main():
    env = ev.active_environment()

    parser = argparse.ArgumentParser(
        description="""Diff two build specs.
(spack-python diffBuildSpecs.py spec1 spec2)

Example usage:

    $ spack spec --yaml dray+mpi > dray-mpi.yaml
    $ spack spec --yaml dray~mpi > dray-nompi.yaml
    $ spack-python lib/scripts/diffBuildSpecs.py --truncate ./dray-mpi.yaml ./dray-nompi.yaml
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-t",
        "--truncate",
        action="store_true",
        help="don't show most details unless they are different",
    )
    parser.add_argument(
        "-d",
        "--diffprint",
        action="store_true",
        help="Print if the two specs are different or the same.",
    )
    parser.add_argument(
        "-a",
        "--asymmetric",
        action="store_true",
        help="Only compare spec0 against spec1. Default behavior also compares spec1 against spec0.",
    )

    parser.add_argument("specs", nargs=argparse.REMAINDER, help="two specs to compare")

    args = parser.parse_args()

    specs = []
    for spec in spack.cmd.parse_specs(args.specs):
        # If the spec has a hash, check it before disambiguating
        spec.replace_hash()
        if spec.concrete:
            specs.append(spec)
        else:
            specs.append(spack.cmd.disambiguate_spec(spec, env))

    if len(specs) != 2:
        raise Exception("Need two specs")

    diff = diff_specs(specs[0], specs[1], truncate=args.truncate)
    diff2 = False
    if not args.asymmetric:
        diff2 = diff_specs(specs[1], specs[0], truncate=args.truncate)
    if args.diffprint:
        diff = diff or diff2
        print(f"DifferentSpecs={diff}")


if __name__ == "__main__":
    main()
