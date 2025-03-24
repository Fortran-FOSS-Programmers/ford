from dataclasses import asdict, dataclass, field
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from markdown_include.include import (  # type: ignore[import]
    INC_SYNTAX as MD_INCLUDE_RE,
    MarkdownInclude,
    IncludePreprocessor,
)

from ford._typing import PathLike
from ford.console import warn
from ford.utils import meta_preprocessor, normalise_path, str_to_bool

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


FAVICON_PATH = Path("favicon.png")

INTRINSIC_MODS = {
    "iso_fortran_env": "http://fortranwiki.org/fortran/show/iso_fortran_env",
    "iso_c_binding": "http://fortranwiki.org/fortran/show/iso_c_binding",
    "ieee_arithmetic": "http://fortranwiki.org/fortran/show/ieee_arithmetic",
    "ieee_exceptions": "http://fortranwiki.org/fortran/show/IEEE+arithmetic",
    "ieee_features": "http://fortranwiki.org/fortran/show/IEEE+arithmetic",
    "openacc": "https://www.openacc.org/sites/default/files/inline-images/Specification/OpenACC.3.0.pdf#page=85",
    "omp_lib": "https://www.openmp.org/spec-html/5.1/openmpch3.html#x156-1890003",
    "mpi": "http://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node410.htm",
    "mpi_f08": "http://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node409.htm",
}

# Mapping from key to separator for settings that are dicts. Required
# due to the legacy format
OPTION_SEPARATORS = {
    "alias": "=",
    "external": "=",
    "extra_mods": ":",
    "extra_vartypes": ":",
}


def default_cpus() -> int:
    try:
        import multiprocessing

        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        return 0


def is_same_type(type_in: Type, tp: Type) -> bool:
    """Returns True if ``type_in`` is the same type as either ``tp``
    or ``Optional[tp]``"""
    return (type_in == tp) or is_optional_type(type_in, tp)


def is_optional_type(tp: Type, sub_tp: Type) -> bool:
    """Returns True if ``tp`` is ``Optional[sub_tp]``"""
    if get_origin(tp) is not Union:
        return False

    return any(tp == sub_tp for tp in get_args(tp))


def convert_to_bool(name: str, option: List[str]) -> bool:
    """Convert value 'option' to a bool, with a nice error message on
    failure. Expects a list from the markdown meta-data extension"""
    if isinstance(option, bool):
        return option

    if len(option) > 1:
        raise ValueError(
            f"Could not convert option '{name}' to bool: expected a single value but got a list ({option})"
        )
    try:
        return str_to_bool(option[0])
    except ValueError:
        raise ValueError(
            f"Could not convert option '{name}' to bool: expected 'true'/'false', got: {option[0]}"
        )


@dataclass
class ExtraFileType:
    extension: str
    comment: str
    lexer: Optional[str] = None

    @classmethod
    def from_string(cls, string: str):
        parts = string.split()
        if not (2 <= len(parts) <= 3):
            raise ValueError(
                f"Unexpected format for 'extra_filetype': expected 'extension comment [lexer]', got {string!r}"
            )

        file_type = cls(parts[0], parts[1])
        if len(parts) == 3:
            file_type.lexer = parts[2]

        return file_type


@dataclass
class ProjectSettings:
    alias: Dict[str, str] = field(default_factory=dict)
    author: Optional[str] = None
    author_description: Optional[str] = None
    author_pic: Optional[str] = None
    bitbucket: Optional[str] = None
    coloured_edges: bool = False
    copy_subdir: List[Path] = field(default_factory=list)
    creation_date: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    css: Optional[Path] = None
    dbg: bool = True
    directory: Path = Path.cwd()
    display: List[str] = field(default_factory=lambda: ["public", "protected"])
    doc_license: str = ""
    docmark: str = "!"
    docmark_alt: str = "*"
    email: Optional[str] = None
    encoding: str = "utf-8"
    exclude: List[str] = field(default_factory=list)
    exclude_dir: List[Path] = field(default_factory=list)
    extensions: List[str] = field(
        default_factory=lambda: ["f90", "f95", "f03", "f08", "f15"]
    )
    external: Dict[str, str] = field(default_factory=dict)
    externalize: bool = False
    extra_filetypes: Dict[str, ExtraFileType] = field(default_factory=dict)
    extra_mods: Dict[str, str] = field(default_factory=dict)
    extra_vartypes: list = field(default_factory=list)
    facebook: Optional[str] = None
    favicon: Path = FAVICON_PATH
    fixed_extensions: List[str] = field(
        default_factory=lambda: ["f", "for", "F", "FOR"]
    )
    fixed_length_limit: bool = True
    force: bool = False
    fpp_extensions: List[str] = field(
        default_factory=lambda: ["F90", "F95", "F03", "F08", "F15", "F", "FOR"]
    )
    github: Optional[str] = None
    gitlab: Optional[str] = None
    gitter_sidecar: Optional[str] = None
    google_plus: Optional[str] = None
    graph: bool = False
    graph_dir: Optional[Path] = None
    graph_maxdepth: int = 10000
    graph_maxnodes: int = 1000000000
    hide_undoc: bool = False
    html_template_dir: List[Path] = field(default_factory=list)
    incl_src: bool = True
    include: List[Path] = field(default_factory=list)
    license: str = ""
    linkedin: Optional[str] = None
    lower: bool = False
    macro: List[str] = field(default_factory=list)
    mathjax_config: Optional[Path] = None
    max_frontpage_items: int = 10
    md_base_dir: Path = Path(".")
    md_extensions: List[str] = field(default_factory=list)
    media_dir: Optional[Path] = None
    output_dir: Path = Path("./doc")
    page_dir: Optional[Path] = None
    parallel: int = default_cpus()
    predocmark: str = ">"
    predocmark_alt: str = "|"
    preprocess: bool = True
    preprocessor: str = "pcpp -D__GFORTRAN__ --passthru-comments"
    print_creation_date: bool = False
    privacy_policy_url: Optional[str] = None
    proc_internals: bool = False
    project: str = "Fortran Program"
    project_bitbucket: Optional[str] = None
    project_download: Optional[str] = None
    project_github: Optional[str] = None
    project_gitlab: Optional[str] = None
    project_sourceforge: Optional[str] = None
    project_url: str = ""
    project_website: Optional[str] = None
    quiet: bool = False
    relative: bool = field(init=False)
    revision: Optional[str] = None
    search: bool = True
    show_proc_parent: bool = False
    sort: str = "src"
    source: bool = False
    src_dir: List[Path] = field(default_factory=lambda: [Path("./src")])
    summary: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    twitter: Optional[str] = None
    version: Optional[str] = None
    warn: bool = False
    website: Optional[str] = None
    year: str = str(date.today().year)

    def __post_init__(self):
        self.relative = self.project_url == ""

        field_types = get_type_hints(self)

        for key, value in asdict(self).items():
            default_type = field_types[key]

            if is_same_type(default_type, type(value)):
                continue

            if get_origin(default_type) is list and not isinstance(value, list):
                setattr(self, key, [value])

        for fixed_extension in self.fixed_extensions:
            if fixed_extension in self.extensions:
                raise ValueError(
                    f"Fixed-form extension '{fixed_extension}' also appears in free-form extension list (`extensions = {self.extensions}`)"
                )

        for mod in self.extra_mods:
            if mod in self.external:
                raise ValueError(f"extra-mod '{mod}' also appears in external mods")

        self.display = [item.lower() for item in self.display]
        self.extensions = list(set(self.extensions) | set(self.fpp_extensions))
        self.exclude_dir.append(self.output_dir)
        self.extra_mods.update(INTRINSIC_MODS)

        # Check that none of the docmarks are the same
        docmarks = ["docmark", "predocmark", "docmark_alt", "predocmark_alt"]
        for first, second in combinations(docmarks, 2):
            first_mark = getattr(self, first)
            second_mark = getattr(self, second)
            if first_mark == second_mark != "":
                raise ValueError(
                    f"{first} ('{first_mark}') and {second} ('{second_mark}') are the same"
                )

        if isinstance(self.extra_filetypes, list):
            try:
                self.extra_filetypes = {
                    filetype.extension: filetype for filetype in self.extra_filetypes
                }
            except AttributeError:
                file_types = [
                    ExtraFileType(**file_type) for file_type in self.extra_filetypes
                ]
                self.extra_filetypes = {
                    file_type.extension: file_type for file_type in file_types
                }

    @classmethod
    def from_markdown_metadata(cls, meta: Dict[str, Any], parent: Optional[str] = None):
        return cls(**convert_types_from_metapreprocessor(cls, meta, parent))

    def normalise_paths(self, directory=None):
        if directory is None:
            directory = Path.cwd()
        self.directory = Path(directory).absolute()
        field_types = get_type_hints(self)

        if self.favicon == FAVICON_PATH:
            self.favicon = Path(__file__).parent / FAVICON_PATH

        if self.md_base_dir == Path("."):
            self.md_base_dir = self.directory

        for key, value in asdict(self).items():
            if value is None:
                continue

            default_type = field_types[key]

            if is_same_type(default_type, List[Path]):
                value = getattr(self, key)
                setattr(self, key, [normalise_path(self.directory, v) for v in value])

            if is_same_type(default_type, Path):
                setattr(self, key, normalise_path(self.directory, value))

        if self.relative:
            self.project_url = self.output_dir


def load_toml_settings(directory: PathLike) -> Optional[ProjectSettings]:
    """Load Ford settings from ``fpm.toml`` file in ``directory``

    Settings should be in ``[extra.ford]`` table
    """

    filename = Path(directory) / "fpm.toml"

    if not filename.is_file():
        return None

    with open(filename, "rb") as f:
        settings = tomllib.load(f)

    if "extra" not in settings:
        return None

    if "ford" not in settings["extra"]:
        return None

    print(f"Reading Ford options from {filename.absolute()}")
    try:
        return ProjectSettings(**settings["extra"]["ford"])
    except ValueError as e:
        raise ValueError(f"Error parsing settings from '{filename}': {e}")


def load_markdown_settings(
    directory: PathLike, project_file: str, filename: Optional[str] = None
) -> Tuple[ProjectSettings, str]:
    settings, project_lines = meta_preprocessor(project_file)
    settings = convert_types_from_metapreprocessor(ProjectSettings, settings, filename)

    # Workaround for file inclusion in metadata
    for option, value in settings.items():
        if isinstance(value, str) and MD_INCLUDE_RE.match(value):
            warn(
                "Including other files in project file metadata is deprecated and "
                "will stop working in a future release.\n"
                f"    {option}: {value}",
            )
            md_base_dir = settings.get("md_base_dir", directory)
            configs = MarkdownInclude({"base_path": str(md_base_dir)}).getConfigs()
            include_preprocessor = IncludePreprocessor(None, configs)
            settings[option] = "\n".join(include_preprocessor.run(value.splitlines()))

    try:
        return ProjectSettings.from_markdown_metadata(settings), "\n".join(
            project_lines
        )
    except ValueError as e:
        raise ValueError(f"Error parsing settings from '{filename}': {e}")


def convert_setting(default_type: Type, key: str, value: Any) -> Any:
    """Convert an individual value's type to be consistent with a given dataclass for the
    given key."""

    if is_same_type(default_type, type(value)):
        # already correct type
        return value
    if is_same_type(default_type, list):
        return [value]
    elif is_same_type(default_type, bool):
        return convert_to_bool(key, value)
    elif is_same_type(default_type, int):
        return int(value[0])
    elif (
        is_same_type(default_type, str) or is_same_type(default_type, Path)
    ) and isinstance(value, list):
        return "\n".join(value)
    elif (get_origin(default_type) is dict) and not isinstance(value, dict):
        resvalue = value
        if isinstance(value, str):
            resvalue = [value]

        # Get rid of any empty strings
        resvalue = [v for v in resvalue if v]

        if get_args(default_type) == (str, ExtraFileType):
            file_types = [ExtraFileType.from_string(string) for string in resvalue]
            return {file_type.extension: file_type for file_type in file_types}
        else:
            sep = OPTION_SEPARATORS[key]
            return _parse_to_dict(resvalue, name=key, sep=sep)

    # Nothing special to do
    return value


def convert_types_from_metapreprocessor(
    cls: Type, settings: Dict[str, Any], parent: Optional[str] = None
):
    """Convert a dict's value's types to be consistent with a given dataclass"""

    field_types = get_type_hints(cls)

    keys_to_drop = []

    for key, value in settings.items():
        try:
            default_type = field_types[key]
        except KeyError:
            prefix = f"In '{parent}': " if parent is not None else ""
            warn(f"{prefix}Ignoring unknown Ford metadata key {key!r}")
            keys_to_drop.append(key)
            continue

        settings[key] = convert_setting(default_type, key, value)

    for key in keys_to_drop:
        settings.pop(key)

    return settings


def convert_types_from_commandarguments(
    settings: ProjectSettings, cargs: Dict[str, Any], parent: Optional[str] = None
):
    """Convert the cargs dict's value's types to be consistent with a given dataclass
    if set and override them in settings.
    """

    field_types = get_type_hints(type(settings))

    for key, value in cargs.items():
        if value is not None:
            if key in field_types:
                setattr(settings, key, convert_setting(field_types[key], key, value))
            else:
                setattr(settings, key, value)

    return settings


def _parse_to_dict(string_list: List[str], name: str, sep: str) -> Dict[str, str]:
    """Parse a list of strings of form "key = value" into a dict

    Parameters
    ----------
    string_list : List[str]
        List of strings to parse
    name : str
        Name in parent settings object, only used for error message
    sep: str
        Separator between key and value

    """

    result = {}
    for string in string_list:
        try:
            key, value = string.split(sep, 1)
        except ValueError:
            raise RuntimeError(
                f"Error setting option {name!r}: expected '{sep}' in {string!r}"
            )

        # Remove extraneous quotes for the URL options
        if sep == ":":
            value.strip().strip(r"\"'")

        result[key.strip()] = value.strip()
    return result


@dataclass
class EntitySettings:
    author: Optional[str] = None
    category: Optional[str] = None
    copy_subdir: List[Path] = field(default_factory=list)
    date: Optional[str] = None
    deprecated: bool = False
    display: List[str] = field(default_factory=list)
    graph: bool = ProjectSettings.graph
    graph_maxdepth: int = ProjectSettings.graph_maxdepth
    graph_maxnodes: int = ProjectSettings.graph_maxnodes
    license: Optional[str] = None
    num_lines: Optional[int] = None
    ordered_subpage: List[str] = field(default_factory=list)
    proc_internals: bool = ProjectSettings.proc_internals
    since: Optional[str] = None
    source: bool = ProjectSettings.source
    summary: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None

    @classmethod
    def from_markdown_metadata(cls, meta: Dict[str, Any], parent: Optional[str] = None):
        return cls(**convert_types_from_metapreprocessor(cls, meta, parent))

    @classmethod
    def from_project_settings(cls, project_settings: ProjectSettings):
        """Inherit entity-specific settings from project-level settings"""
        return cls(
            graph=project_settings.graph,
            graph_maxdepth=project_settings.graph_maxdepth,
            graph_maxnodes=project_settings.graph_maxnodes,
            proc_internals=project_settings.proc_internals,
            source=project_settings.source,
        )

    def update(self, metadata: Dict[str, Any], parent: Optional[str] = None) -> None:
        """Update self with values from a dict"""
        current_settings = asdict(self)
        current_settings.update(
            convert_types_from_metapreprocessor(type(self), metadata, parent)
        )
        for key, value in current_settings.items():
            setattr(self, key, value)
