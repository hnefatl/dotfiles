# Dotfiles

My personal dotfile collection.

These are written using Jinja2 template formatting, with `deploy.py` rendering the templates and installing the results.

This system is designed for a specific set of features/constraints:

-   deployment over multiple computers with different setups and org policies: my home PC, work laptop, personal laptop. This meant I can't rely just on e.g. Nix.
    -   Jinja2 templates allow for expanding different values into config files on different machines, based on the attributes of that machine.
-   mutable dotfiles, so they can be modified by e.g. `rustup` or other utilities without too much hassle.
    -   combined with a workflow that makes it easy to copy those changes back up to the templates, rather than 

## Configuring

### `machine_config.txt`

Each install needs a file called `machine_config.txt` at the root of the repo, containing one of the keys from `machine_configs.MACHINE_CONFIGS`. This selects which machine configuration to install on the local machine, and isn't persisted in version control.

If the file doesn't exist when `deploy.py` is run, the tool will offer to create the file from one of the defined machine configurations.

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