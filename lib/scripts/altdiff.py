import spack.cmd
import spack.environment as ev
import spack.traverse as traverse
from llnl.util.tty.color import cwrite

import sys


def diff_specs(spec_a, spec_b):
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
        def __init__(self, spec):
            self.variants = spec.variants

        def compare(self, other_spec):
            if not self.variants:
                return
            for k, v in self.variants.items():
                if k not in other_spec.variants:
                    highlight(_variant_str(v))
                elif not v.satisfies(other_spec.variants[k]):
                    highlight(_variant_str(v))
                else:
                    _write(_variant_str(v))

    class VersionComparator:
        def __init__(self, spec):
            self.version = spec.version

        def compare(self, other_spec):
            other_version = other_spec.version
            if self.version.satisfies(other_version):
                _write(f"@{self.version}")
            else:
                highlight(f"@{self.version}")

    class CompilerComparator:
        def __init__(self, spec):
            self.compiler = spec.compiler

        def compare(self, other_spec):
            other_cmp = other_spec.compiler
            if self.compiler.name == other_cmp.name:
                _write(f"%{self.compiler.name}")
                if self.compiler.version.satisfies(other_cmp.version):
                    _write(f"@{self.compiler.version}")
                else:
                    highlight(f"@{self.compiler.version}")
            else:
                highlight(f"%{self.compiler}")

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
        def __init__(self, spec):
            self.arch = spec.architecture

        def _component_wise_diff(self, x, y, separator):
            pairs = list(zip(x, y))
            size = len(pairs)
            for i, (xi, yi) in enumerate(pairs):
                if xi == yi:
                    _write(xi)
                else:
                    highlight(f"{xi}/{yi}")
                if i < size - 1:
                    _write(separator)

        def compare(self, other_spec):
            this = [self.arch.platform, self.arch.os, str(self.arch.target)]
            other_arch = other_spec.architecture
            other = [other_arch.platform, other_arch.os, str(other_arch.target)]
            other[2] = "foo"
            if this == other:
                _write(f" arch={self.arch}")
            else:
                _write(" arch=")
                self._component_wise_diff(this, other, "-")

    class NewlineWithDepthIndent:
        def __init__(self):
            self.depth = 0

        def __call__(self):
            print()
            _write("  " * self.depth)

    nl_cb = NewlineWithDepthIndent()

    def decompose(spec):
        return [
            VersionComparator(spec),
            CompilerComparator(spec),
            VariantsComparator(spec),
            ArchComparator(spec),
            DepsComparator(spec, nl_cb),
        ]

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
        print()  # New line


def main():
    env = ev.active_environment()

    specs = []
    for spec in spack.cmd.parse_specs(sys.argv[1:]):
        # If the spec has a hash, check it before disambiguating
        spec.replace_hash()
        if spec.concrete:
            specs.append(spec)
        else:
            specs.append(spack.cmd.disambiguate_spec(spec, env))

    if len(specs) != 2:
        raise Exception("Need two specs")

    diff_specs(specs[0], specs[1])


if __name__ == "__main__":
    main()
