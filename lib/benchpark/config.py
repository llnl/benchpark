import benchpark.paths

import pathlib
import yaml


class RequiredClassAttr:
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, owner):
        raise NotImplementedError(
            f"{owner.__name__} must define class attribute '{self.name}'"
        )


class ConfigSection:
    def __init__(self, data, path):
        self.data = data
        self.path = pathlib.Path(path)

    filename = RequiredClassAttr("filename")
    name = RequiredClassAttr("section")

    @classmethod
    def try_load(cls, cfg_dir):
        cfg_path = pathlib.Path(cfg_dir) / cls.filename
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                data = yaml.safe_load(f)
                return cls(data[cls.section], cfg_path)

    def resolve_path(self, value):
        path = pathlib.Path(value)
        if not path.is_absolute():
            return (self.path.parents[0] / path).resolve()


class PropertyDict:
    def __getattr__(self, name):
        val = self.data[name]
        if isinstance(val, dict):
            return PropertyDict(val)
        return val


class Repos(ConfigSection, PropertyDict):
    filename = "repos.yaml"
    name = "repos"


_section_types = [
    Repos
]


class Configuration:
    section_names = [st.name for st in _section_types]

    def __init__(self, cfg_dir):
        self.sections = {}
        for st in _section_types:
            attempt = st.try_load(cfg_dir)
            if attempt:
                self.sections[st.name] = attempt

    def __getattr__(self, name):
        if name in self.sections:
            return self.sections[name]
        elif name in Configuration.section_names:
            raise Exception("This section is not present in this config")
        else:
            raise AttributeError("No such section")


_unset = object()


_user_input_cfg = _unset


def determine_config():
    """
    Benchpark configs don't merge or override like Spack/Ramble. You
    just point it at a directory and that's where all your config is.
    """
    if _user_input_cfg is _unset:
        raise Exception("Internal error: config initialization")
    elif _user_input_cfg:
        if not _user_input_cfg.exists():
            raise Exception(f"Specific config dir does not exist: {_user_input_cfg}")
        else:
            return Configuration(_user_input_cfg)

    possible_dirs = [
        benchpark.paths.invocation_working_dir / "benchpark-config",
        benchpark.paths.benchpark_root / "config"
    ]
    for pd in possible_dirs:
        if pd.exists():
            return Configuration(pd)


_configuration = None


def configuration():
    global _configuration
    if not _configuration:
        _configuration = determine_config()

    return _configuration
    