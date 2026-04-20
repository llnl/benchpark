import sys
from pathlib import Path

import spack.config as config


def find_dir(root, target_name):
    root = Path(root)
    for path in root.rglob("*"):
        if path.is_dir() and path.name == target_name:
            return path.resolve()
    return None


def main(benchpark_wkp_dir):
    base_dir = Path(__file__).resolve().parents[0]
    git_repos_dir = base_dir / "git-repos"

    cfg_path = find_dir(benchpark_wkp_dir, "auxiliary_software_files")
    ds = config.DirectoryConfigScope("auxpath", cfg_path)
    cfg = config.create_from(ds)
    pkgs_cfg = cfg.get("packages")

    for repo_path in git_repos_dir.iterdir():
        pkg_name = repo_path.parts[-1]
        pkg_cfg = pkgs_cfg.setdefault(pkg_name, {})
        attrs_cfg = pkg_cfg.setdefault("package_attributes", {})
        attrs_cfg["git"] = str(repo_path)

    # import pdb; pdb.set_trace()
    cfg.set("packages", pkgs_cfg, "auxpath")


if __name__ == "__main__":
    main(sys.argv[1])
