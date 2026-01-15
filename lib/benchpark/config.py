import pathlib
import yaml


def determine_config():
    """
    Benchpark configs don't merge or override like Spack/Ramble. You
    just point it at a directory and that's where all your config is.
    """
    pass


class RequiredClassAttr:
    def __get__(self, obj, owner):
        raise NotImplementedError(
            f"{owner.__name__} must define class attribute 'filename'"
        )


class ConfigSection:
    def __init__(self, data):
        self.data = data

    filename = RequiredClassAttr()
    section = RequiredClassAttr()

    @classmethod
    def try_load(cls, cfg_dir):
        cfg_path = pathlib.Path(cfg_dir) / cls.filename
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                return cls(yaml.load(f)[cls.section])


class PropertyDict:
    def __getattr__(self, name):
        val = self.data[name]
        if isinstance(val, dict):
            return PropertyDict(val)
        return val


class Repos(ConfigSection):
    filename = "repos.yaml"
    section = "repos"

    @property
    def system_repos(self):
        return self.data["systems"]

    @property
    def experiment_repos(self):
        return self.data["experiments"]

    @property
    def application_repos(self):
        return self.data["applications"]


_section_types = [
    Repos
]


class Configuration:
    def __init__(self, cfg_dir):
        self.sections = {}
        for st in _section_types:
            attempt = st.try_load(cfg_dir)
            if attempt:
                self.sections[st.section] = attempt