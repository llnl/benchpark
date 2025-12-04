import json
import sys

import spack.environment as ev


def main():
    x = ev.active_environment()
    y = list(x.concrete_roots())
    # There may be multiple roots in the env. Assume that the experiment of
    # interest is the largest dag (every other root should just be an attempt
    # to constrain dependencies of this experiment).
    z = max(y, key=lambda i: sum(1 for _ in i.traverse()))
    built_specs = list()
    for dep in z.traverse(deptype="link"):
        if dep.external:
            continue
        if "runtime" in getattr(dep.package, "tags", []):
            continue
        built_specs.append(dep)

    urls = {}
    for spec in built_specs:
        x = spec.package.stage[0].default_fetcher
        if hasattr(x, "url"):
            urls[spec.name] = {
                "url": x.url,
                "details": spec.package.versions[spec.version],
            }
        else:
            raise Exception(f"Unexpected: {spec.name} has no url attribute")

    result = {
        "root": z.name,
        "tree": z.tree(),
        "info": [(w.name, w.package.install_env_path) for w in built_specs],
        "urls": urls,
    }
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
