# LEmmA Near Field Measurement System

## Installation

To quickly install the environment to run `xnft`, follow the steps below:

1. Install Pixi package manager: https://pixi.prefix.dev/latest/installation/
2. Install the `default` environment by running: 
    ```shell
    pixi install
    ```
3. Launch `xnft` by running: 
    ```shell
    pixi run xnft
    ```

## Development

...

### Upgrading Dependencies

> [!warning] 
> Upgrading all dependencies may break software due to incompatible changes in newer versions of libraries.

To upgrade dependencies listed in the `pyproject.toml` using pixi, run 
```shell
pixi upgrade <packages>
```
Omitting the `<packages>` will upgrade _all_ packages.  It may be useful to first run this using the `--dry-run` flag to only print the packages which will be upgraded prior to actually commiting the changes to the file.
