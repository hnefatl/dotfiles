from typing import Any

import dataclasses
import os
import pathlib


def _get_path_binaries() -> set[str]:
    """Get all binaries accessible from `$PATH`."""
    binaries = set[str]()
    for dir in os.environ["PATH"].split(":"):
        p = pathlib.Path(dir)
        if not p.is_dir():
            continue
        for e in p.iterdir():
            if e.is_file() and os.access(e, os.X_OK):
                binaries.add(e.name)
    return binaries


_PATH_BINARIES = frozenset(_get_path_binaries())


@dataclasses.dataclass(frozen=True)
class MachineConfig:
    work: bool
    shell: str
    laptop: bool
    pc: bool
    window_manager: str
    primary_display: str
    statusbar_displays: frozenset[str]
    other_displays: frozenset[str]
    path_binaries: frozenset[str] = _PATH_BINARIES

    def as_template_variables(self) -> dict[str, Any]:
        """Get variables as a dict of the form `{"KEY": <typed value>, ...}`."""
        return {k.upper(): v for k, v in dataclasses.asdict(self).items()}


MACHINE_CONFIGS: dict[str, MachineConfig] = {
    "home_pc": MachineConfig(
        work=False,
        shell="zsh",
        laptop=False,
        pc=True,
        window_manager="i3",
        primary_display="DP-0",
        statusbar_displays=frozenset(),
        other_displays=frozenset({"HDMI-0"}),
    ),
    "work_laptop": MachineConfig(
        work=True,
        shell="zsh",
        laptop=True,
        pc=False,
        window_manager="i3",
        primary_display="eDP-1",
        statusbar_displays=frozenset({"DP-3", "DP-3-8"}),
        other_displays=frozenset({"DP-3-1-8"}),
    ),
}


def should_install_directory(config: MachineConfig) -> dict[str, bool]:
    return {
        "bashrc": config.shell == "bash",
        "dunst": "dunst" in config.path_binaries,
        "i3": "i3" in config.path_binaries,
        "i3blocks": "i3" in config.path_binaries,
        "terminator": "terminator" in config.path_binaries,
        "vim": "vim" in config.path_binaries,
        # Currently only work laptop needs these tweaks.
        "xmodmap": config.work,
        "xsession": config.work,
    }
