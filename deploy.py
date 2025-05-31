#!/usr/bin/env python

import dataclasses
from typing import Optional, Self

import click
import jinja2
import os
import pathlib

import diff


def load_config_file(path: pathlib.Path) -> dict[str, str]:
    """Load a generic `variable=value` line-by-line file."""
    vars = dict[str, str]()
    for line in path.read_text().splitlines():
        if line.startswith("#") or line.startswith("//") or not line.strip():
            continue
        [var, val] = line.split("=", maxsplit=1)
        vars[var] = val
    return vars


def load_variables(path: pathlib.Path) -> dict[str, str | bool]:
    """Special case config file load, handling Python<->Jinja types."""
    vars = dict[str, str | bool]()
    for var, val in load_config_file(path).items():
        # Jinja is aware of types, so e.g. `{% if foo %}` requires `foo` to be a boolean.
        if val.title() in ("True", "False"):
            val = val.title() == "True"
        vars[var] = val
    return vars


def get_path_binaries() -> set[str]:
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


@dataclasses.dataclass(frozen=True)
class TemplateFile:
    output_path: pathlib.Path
    template: jinja2.Template

    @property
    def template_path(self) -> pathlib.Path:
        assert self.template.filename is not None
        return pathlib.Path(self.template.filename)

    def render(self) -> str:
        # Jinja seems to strip the trailing newline, leaving diff artefacts.
        return self.template.render() + "\n"

    def read_existing(self) -> Optional[str]:
        try:
            return self.output_path.read_text()
        except FileNotFoundError:
            return None

    def has_diff(self) -> bool:
        # Special case: if the generated file is empty, don't create the file if it doesn't already exist.
        # This allows for not installing e.g. a bashrc config if the shell isn't bash - we just make the
        # file empty.
        if self.render().strip() == "" and not self.output_path.exists():
            return False
        return self.read_existing() != self.render()

    def print_diff(self, context_lines: int):
        existing = self.read_existing() or ""
        print(f"Diff to apply from '{self.template_path}' to '{self.output_path}':")
        diff.pretty_print(
            diff.diff(existing, self.render()), context_lines=context_lines
        )

    def write(self):
        self.output_path.write_text(self.render())

    @classmethod
    def create(
        cls,
        env: jinja2.Environment,
        output_dir: pathlib.Path,
        template_path: pathlib.Path,
    ) -> Self:
        template = env.get_template(str(template_path))
        output_path = output_dir.joinpath(*template_path.parts[1:])
        return cls(output_path, template)


@click.command()
@click.option(
    "--variable_file",
    default=pathlib.Path("variables.txt"),
    help="Path to file holding variable definitions for this install.",
    type=pathlib.Path,
)
@click.option(
    "--install_if_file",
    default=pathlib.Path("install_if.txt"),
    help="Path to file holding conditional installation expressions for this install.",
    type=pathlib.Path,
)
@click.option(
    "--config_dir",
    default=pathlib.Path("configs"),
    help="Path to directory holding dotfile configurations.",
    type=pathlib.Path,
)
@click.option(
    "--output_dir",
    default=pathlib.Path.home(),
    help="Path to directory to write generated configs to. Defaults to $HOME if not set.",
    type=pathlib.Path,
)
@click.option(
    "--diff_only", default=False, help="Whether to only print diffs, no editors."
)
@click.option(
    "--diff_context_lines",
    default=2,
    help="How many lines of context to print in the diff view.",
)
def main(
    variable_file: pathlib.Path,
    install_if_file: pathlib.Path,
    config_dir: pathlib.Path,
    output_dir: pathlib.Path,
    diff_only: bool,
    diff_context_lines: int,
):
    variables = {
        "PATH_BINARIES": get_path_binaries(),
        **load_variables(variable_file),
    }
    install_if = load_config_file(install_if_file)
    loader = jinja2.FileSystemLoader(searchpath=str(config_dir))
    env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
    env.globals.update(variables)  # type: ignore

    for template_name in loader.list_templates():
        template_path = pathlib.Path(template_name)
        if template_path.is_absolute():
            raise ValueError(f"Unsupported absolute template path: {template_path}")

        # If the directory has an associated conditional expression, only install if it's met.
        if install_if_expression := install_if.get(template_path.parts[0]):
            if not env.compile_expression(install_if_expression)(variables):
                continue

        click.clear()
        while True:
            try:
                file = TemplateFile.create(env, output_dir, template_path)
            except Exception as e:
                raise RuntimeError(f"Failed while loading {template_name}") from e
            if not file.has_diff():
                break

            file.print_diff(diff_context_lines)

            if diff_only:
                break

            print("[e]dit, [r]efresh, [s]kip, [o]verwrite, [q]uit")
            command = click.getchar()
            if command == "e":
                click.edit(filename=[str(file.template_path), str(file.output_path)])
            elif command == "r":
                continue
            elif command == "s":
                break
            elif command == "o" and click.confirm(text="Are you sure?"):
                file.write()
                break
            elif command == "q":
                return


if __name__ == "__main__":
    main()
