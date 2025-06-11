#!/usr/bin/env python

import dataclasses
from typing import Optional, Self

import click
import jinja2
import pathlib

import diff
import machine_configs


def load_or_create_configuration_file(
    path: pathlib.Path,
) -> Optional[machine_configs.MachineConfig]:
    if not path.exists():
        print(
            f"'{path}' does not exist. Select an existing config or update `variables.py` ([q]uit):"
        )
        config_names = list(sorted(machine_configs.MACHINE_CONFIGS.keys()))
        for i, config_name in enumerate(config_names):
            print(f"[{i}]: {config_name}")
        while True:
            index = click.getchar()
            if index == "q":
                return None
            try:
                config_name = config_names[int(index)]
                break
            except (IndexError, ValueError):
                print("Invalid selection.")
        path.write_text(config_name)

    return machine_configs.MACHINE_CONFIGS[path.read_text()]


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

    def write_output_path(self):
        self.output_path.write_text(self.render())
    def write_template_path(self):
        self.template_path.write_bytes(self.output_path.read_bytes())

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
    "--machine_config_file",
    default=pathlib.Path("machine_config.txt"),
    help="Path to file holding machine configuration name for this install.",
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
    machine_config_file: pathlib.Path,
    config_dir: pathlib.Path,
    output_dir: pathlib.Path,
    diff_only: bool,
    diff_context_lines: int,
):
    if not (machine_config := load_or_create_configuration_file(machine_config_file)):
        return
    should_install_directory = machine_configs.should_install_directory(machine_config)

    loader = jinja2.FileSystemLoader(searchpath=str(config_dir))
    env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
    env.globals.update(machine_config.as_template_variables())  # type: ignore

    for template_name in loader.list_templates():
        template_path = pathlib.Path(template_name)
        if template_path.is_absolute():
            raise ValueError(f"Unsupported absolute template path: {template_path}")

        # Skip directories where the installation condition isn't met.
        if not should_install_directory.get(template_path.parts[0], True):
            continue

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

            print("[e]dit, [r]efresh, [s]kip, [o]verwrite destination, overwrite [t]emplate, [c]lear, [q]uit")
            command = click.getchar()
            if command == "e":
                click.edit(filename=[str(file.template_path), str(file.output_path)])
            elif command == "r":
                continue
            elif command == "s":
                break
            elif command == "o" or command == "t":
                print("Are you sure? [y/n]")
                if click.getchar() == "y":
                    if command == "o":
                        file.write_output_path()
                    else:
                        file.write_template_path()
                    break
            elif command == "c":
                click.clear()
            elif command == "q":
                return


if __name__ == "__main__":
    main()
