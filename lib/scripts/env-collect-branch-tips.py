import os
import shutil
import sys

import spack.environment as ev
from spack.fetch_strategy import GitFetchStrategy


def main():
    destination = sys.argv[1]

    e = ev.active_environment()
    for _, spec in e.concretized_specs():
        df = spec.package.stage[0].default_fetcher
        if not df.cachable and isinstance(df, GitFetchStrategy):
            df.get_full_repo = True
            pkg_dst = os.path.join(destination, spec.name)
            if not os.path.exists(pkg_dst):
                spec.package.stage.fetch()
                shutil.move(spec.package.stage.source_path, pkg_dst)
            print(f"{spec.name}")


if __name__ == "__main__":
    main()
