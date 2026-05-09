import os
import shutil
import sys

import spack.environment as ev
import spack.repo
from spack.fetch_strategy import GitFetchStrategy


def main():
    destination = sys.argv[1]

    e = ev.active_environment()
    for spec in e.all_specs():
        if spec.external:
            continue
        pkg_cls = spack.repo.PATH.get_pkg_class(spec.name)
        derived_spec = spack.spec.Spec(spec.name)
        derived_spec.versions = spec.versions
        pkg_obj = pkg_cls(derived_spec)
        df = pkg_obj.stage[0].default_fetcher
        if not df.cachable and isinstance(df, GitFetchStrategy):
            df.get_full_repo = True
            pkg_dst = os.path.join(destination, spec.name)
            if not os.path.exists(pkg_dst):
                pkg_obj.stage.fetch()
                shutil.move(pkg_obj.stage.source_path, pkg_dst)
            print(f"{spec.name}")


if __name__ == "__main__":
    main()
