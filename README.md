# ipolDevel
This repository contains the source code of the demo system of the Image Processing On Line (IPOL) platform along with its LaTeX documentation.

The official repository is here: [https://github.com/ipol-journal/ipolDevel](https://github.com/ipol-journal/ipolDevel)

Always a work in progress...

[https://www.ipol.im](https://www.ipol.im)

## How to contribute

The IPOL demo system is using Python 3.9. Your contributions should pass basic codestyle checks: ruff, isort, black.
These tools can be installed using pip, and run with:
```
ruff . --fix
black cp2 ipol_demo
isort cp2 ipol_demo
```

See the [Github Actions workflow](.github/workflows/python.yaml) for more details and specific tool versions. See [pyproject.toml](pyproject.toml) for the tools settings.
