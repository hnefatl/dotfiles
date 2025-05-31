#!/usr/bin/env python

import dataclasses
from typing import Optional, Self

import jinja2
import pathlib
import click

import diff


def load_config_file(path: pathlib.Path) -> dict[str, str]:
    """Load a generic `variable=value` line-by-line file."""
    vars = dict[str, str]()
    for line in path.read_text().splitlines():
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


@dataclasses.dataclass(frozen=True)
class TemplateFile:
    output_path: pathlib.Path
    template: jinja2.Template

    @property
    def template_path(self) -> pathlib.Path:
        assert self.template.filename is not None
        return pathlib.Path(self.template.filename)

    def render(self) -> str:
        return self.template.render()

    def read_existing(self) -> Optional[str]:
        try:
            return self.output_path.read_text()
        except FileNotFoundError:
            return None

    def has_diff(self) -> bool:
        # Special case: if the generated file is empty, don't create the file if it doesn't already exist.
        # This allows for not installing e.g. a bashrc config if the shell isn't bash - we just make the
        # file empty.
        if self.render().strip() == "" and self.read_existing() is None:
            return False
        return self.read_existing() != self.render()

    def print_diff(self):
        existing = self.read_existing() or ""
        diff.pretty_print(diff.diff(existing, self.render()))

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
def main(
    variable_file: pathlib.Path,
    install_if_file: pathlib.Path,
    config_dir: pathlib.Path,
    output_dir: pathlib.Path,
    diff_only: bool,
):
    variables = load_variables(variable_file)
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
            file = TemplateFile.create(env, output_dir, template_path)
            if not file.has_diff():
                break

            print(f"Diff between '{file.template_path}' and '{file.output_path}':")
            file.print_diff()

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
