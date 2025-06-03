# Dotfiles

My personal dotfile collection.

These are written using Jinja2 template formatting, with `deploy.py` rendering the templates and installing the results.

This system is designed for a specific set of features/constraints:

-   deployment over multiple computers with different setups and org policies: my home PC, work laptop, personal laptop. This meant I can't rely just on e.g. Nix.
    -   Jinja2 templates allow for expanding different values into config files on different machines, based on the attributes of that machine.
-   mutable dotfiles, so they can be modified by e.g. `rustup` or other utilities without too much hassle.
    -   combined with a workflow that makes it easy to copy those changes back up to the templates, rather than 

## Configuring

### `variables.txt`

Each install needs a file called `variables.txt` at the root of the repo, in the format:

```python
WORK=False
LAPTOP=True
SHELL="zsh"
MY_LIST={"foo", "bar"}
```

This is interpreted as `<variable>=<python expression>`, with all variables being available in the templated config files. Python expressions are evaluated with support for sets such that e.g. `{% "foo" in MY_LIST %}` works as expected.

#### Creation from template

If `deploy.py` is run without an existing `variables.txt` file, an option to symlink one from inside `variables_templates/` will be offered.

#### `PATH_BINARIES`

One additional variable is added to the variable set available in templates: `PATH_BINARIES`. This is the set of filenames of all executable files found in `$PATH` directories.

### `install_if.txt`

An install may include a file `install_if.txt` at the root of the repo, in the format:

```ini
bashrc=SHELL == "bash"
dunst="dunst" in PATH_BINARIES
```

This is interpreted as `<config subdirectory>=<jinja2 expression>`: if a subdirectory of `configs/` matches the key, then the templates within will only be processed if the Jinja2 expression evaluates to `true`.

This allows excluding whole subtrees of configs if they're not relevant to this machine.

## Deployment

On Nix, `nix-shell` handles the development and deployment environment:

```shell
$ nix-shell
$ ./deploy.py
```

On other systems, create and enter a python virtual environment before running `deploy.py`:

```shell
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install --user -r requirements.txt
$ ./deploy.py
```