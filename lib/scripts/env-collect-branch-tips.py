import sys
import json

import spack.repo
from spack.fetch_strategy import GitFetchStrategy

# Spack >= 1.3.0 moved active_environment to its own module
try:
    from spack.active_environment import active_environment
except ImportError:
    # Fall back to older Spack versions
    from spack.environment import active_environment


def main():
    # Dictionary mapping package name to requirement spec
    requirements = {}

    e = active_environment()
    for spec in e.all_specs():
        if spec.external:
            continue
        pkg_cls = spack.repo.PATH.get_pkg_class(spec.name)
        derived_spec = spack.spec.Spec(spec.name)
        derived_spec.versions = spec.versions
        pkg_obj = pkg_cls(derived_spec)
        df = pkg_obj.stage[0].default_fetcher

        # Identify branch-based packages (not tags or explicit commits)
        # Branch-based versions need commit pinning for offline builds since branches can move
        # Tag-based versions can use cached tarballs since tags are immutable
        if isinstance(df, GitFetchStrategy) and (df.branch or not df.cachable):
            # Extract the commit from the concretized spec
            commit = None
            if hasattr(spec, "variants") and "commit" in spec.variants:
                commit = str(spec.variants["commit"].value)

            if commit:
                version_str = str(spec.version)
                # Create requirement spec: @version commit=hash
                require_spec = f"@{version_str} commit={commit}"
                requirements[spec.name] = require_spec

    # Output as JSON to stdout for easy parsing
    print(json.dumps(requirements, indent=2))


if __name__ == "__main__":
    main()
