import spack.environment as ev
import json
import sys

def main():
    x = ev.active_environment()
    y = list(x.concrete_roots())
    # There may be multiple roots in the env. Assume that the experiment of
    # interest is the largest dag (every other root should just be an attempt
    # to constrain dependencies of this experiment).
    z = max(y, key=lambda i: sum(1 for _ in i.traverse()))
    built_packages = list(dep for dep in z.traverse() if not dep.external)
    result = {
        "root": z.name,
        "tree": z.tree(),
        "info": [(w.name, w.package.install_env_path) for w in built_packages]
    }
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
