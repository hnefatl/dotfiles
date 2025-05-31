let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (python-pkgs: [
      python-pkgs.black
      python-pkgs.pip
      python-pkgs.venvShellHook
    ]))
  ];

  # Tweaked from https://www.reddit.com/r/NixOS/comments/1c5rrxl/comment/kzw7s97
  shellHook = ''
    SOURCE_DATE_EPOCH=$(date +%s)
    export VIRTUAL_ENV_DISABLE_PROMPT=1
    VENV=.venv

    if test ! -d $VENV; then
      python3.12 -m venv $VENV
    fi
    source ./$VENV/bin/activate
    pip install -r requirements.txt
  '';
}