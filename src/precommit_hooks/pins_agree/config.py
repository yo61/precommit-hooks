"""`.pins-agree.toml`: the groups of pins that must name one version."""

from __future__ import annotations

import re
import tomllib
from collections import Counter
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

DEFAULT_PATH = Path(".pins-agree.toml")


class ConfigError(ValueError):
    """The configuration file is missing, is not TOML, or does not validate."""


class Pin(BaseModel):
    """One place a version is written: the files a glob matches, and a line pattern.

    Every line of every matching file that `pattern` matches is an occurrence; its
    `version` group is the version written there.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    file: str = Field(min_length=1)
    pattern: re.Pattern[str]

    @field_validator("file")
    @classmethod
    def _inside_the_repository(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("must be relative to the repository root, without '..'")
        return value

    @field_validator("pattern")
    @classmethod
    def _has_a_version_group(cls, value: re.Pattern[str]) -> re.Pattern[str]:
        if "version" not in value.groupindex:
            raise ValueError("must have a named group (?P<version>...)")
        return value


class Group(BaseModel):
    """Pins that must all name the same version."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    name: str = Field(min_length=1)
    pins: list[Pin] = Field(min_length=1, alias="pin")


class Config(BaseModel):
    """Every group the hook checks."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    groups: list[Group] = Field(min_length=1, alias="group")

    @field_validator("groups")
    @classmethod
    def _names_are_unique(cls, value: list[Group]) -> list[Group]:
        repeated = sorted(name for name, n in Counter(g.name for g in value).items() if n > 1)
        if repeated:
            raise ValueError(f"names must be unique; repeated: {', '.join(repeated)}")
        return value


def load(path: Path) -> Config:
    """Read and validate a configuration file.

    Args:
        path: The TOML file to read.

    Returns:
        The validated configuration.

    Raises:
        ConfigError: If the file is missing, is not valid TOML, or does not validate. The
            message starts with the path and names each failing field.
    """
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"{path}: not found; create it with at least one [[group]]") from None
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: not valid TOML: {exc}") from None
    try:
        return Config.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"{path}: {_describe(exc)}") from None


def _describe(exc: ValidationError) -> str:
    problems = []
    for error in exc.errors():
        where = ".".join(str(part) for part in error["loc"])
        message = error["msg"].removeprefix("Value error, ")
        problems.append(f"{where}: {message}")
    return "; ".join(problems)
