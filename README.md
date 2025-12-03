# LEmmA Near Field Measurement System

## Installation

...

## Development

...

### Upgrading Dependencies

> [!warning] Upgrading all dependencies may break software due to incompatible changes in newer versions of libraries.

To upgrade dependencies listed in the `pyproject.toml` using pixi, run 
```shell
pixi upgrade <packages>
```
Omitting the `<packages>` will upgrade _all_ packages.  It may be useful to first run this using the `--dry-run` flag to only print the packages which will be upgraded prior to actually commiting the changes to the file.
