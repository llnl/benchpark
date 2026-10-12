import os
import shutil
import sys

import spack.repo
from spack.fetch_strategy import GitFetchStrategy

# Spack >= 1.3.0 moved active_environment to its own module
try:
    from spack.active_environment import active_environment
except ImportError:
    # Fall back to older Spack versions
    from spack.environment import active_environment


def main():
    destination = sys.argv[1]

    e = active_environment()
    for spec in e.all_specs():
        if spec.external:
            continue
        pkg_cls = spack.repo.PATH.get_pkg_class(spec.name)
        derived_spec = spack.spec.Spec(spec.name)
        derived_spec.versions = spec.versions
        pkg_obj = pkg_cls(derived_spec)
        df = pkg_obj.stage[0].default_fetcher
        # Mirror git packages that use branches (not tags or explicit commits)
        # Branch-based versions need the full repo for offline builds since branches can move
        # Tag-based versions can use cached tarballs since tags are immutable
        if isinstance(df, GitFetchStrategy) and (df.branch or not df.cachable):
            df.get_full_repo = True
            pkg_dst = os.path.join(destination, spec.name)
            if not os.path.exists(pkg_dst):
                pkg_obj.stage.fetch()
                shutil.move(pkg_obj.stage.source_path, pkg_dst)
            print(f"{spec.name}")


if __name__ == "__main__":
    main()
