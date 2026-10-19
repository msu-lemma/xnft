# Installing _xNFT_

## Table of Contents

1. [Install via Package (pip/conda/pixi)](#install-via-package-pipcondapixi)
2. [Install From Source](#installing-from-source)
3. [Build Distributable Package with Embedded Dependencies (Optional)](#build-distributable-package-optional)

## Install via Package (pip/conda/pixi)

> [!warning] 🚧 Work in progress 🚧
> Please follow the instructions in **[Installing From Source](#installing-from-source)**

### Package Sources

> [!NOTE]
> Installation via PyPI and conda-forge are not yet supported.

Packaged versions of _xNFT_ are provided in `.conda` (conda/pixi format) and `.whl` (pip format) which can be found at the links in the following section.

#### Latest Release Packages

The latest release can be downloaded from **[Releases](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases)**.   Each release contains `.conda` and `.whl` artifacts to install.

- **[Latest Release](https://gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases/permalink/latest)**

#### Latest Development Packages

Development packages are generated from the `main` branch which contain the latest features and bug fixes but may be less stable than the [latest release packages](#latest-release-packages). Each build contains `.conda` and `.whl` artifacts to install.

- **[Development Packages](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/packages/)**

<!-- - **[Current development conda package](https://gitlab.msu.edu/api/v4/projects/28094/jobs/artifacts/main/raw/dist/xnft-0.0.0.dev0-pyh4616a5c_0.conda?job=package)** (from `main`)
- **[Current development wheel](https://gitlab.msu.edu/api/v4/projects/28094/jobs/artifacts/main/raw/dist?job=package)** (from `main`) -->

##### PyPI Package Install

The latest development wheel package can also be installed directly from the via `pip` by running:

```shell
pip install xnft --index-url https://www.gitlab.msu.edu/api/v4/projects/28094/packages/pypi/simple
```

> [!note]
> When using PyPI, it is recommended to use an environment manager such as [conda](https://docs.conda.io/projects/conda/en/stable/), [pixi](https://pixi.prefix.dev/latest/), [venv](https://docs.python.org/3/library/venv.html), or [pipenv](https://pipenv.pypa.io/en/latest/) to minimize package conflicts with system Python installs.

> [!warning]
> The PyPI link above will not work until the package is made fully public.

### Installation

## Installing From Source

To install _xNFT_ from source, it is recommended to use Pixi to manage the environment (<https://pixi.prefix.dev/latest/>).

### Prerequisites

1. Install Pixi package manager by following the steps at: <https://pixi.prefix.dev/latest/installation/>

   After installation, you may need to close and re-open your terminal to properly source the Pixi executable.  Verify the installation was successful by running:

   ```sh
   pixi --version
   ```

2. Install `git` and `git-lfs`. This may be installed via the OS package manager or pixi.

   Choose only **_one_** option below:
    - **Windows (Winget):** In any "PowerShell" run:

        ```PowerShell
        winget install --id Git.Git -e --source winget
        ```

    - **macOS or Linux (Pixi):** in a terminal run:

        ```sh
        pixi global install --environment git --expose git git-lfs
        ```

        This will add the `git` and `git-lfs` executables to a global directory (typically in your home folder) and add the `git` executable to your terminal's search path.

    - **macOS (Homebrew):** In terminal install via [Homebrew](https://brew.sh):

        ```sh
        brew install git git-lfs
        ```

    - **Ubuntu or Debian (APT):** In terminal install via apt:

        ```sh
        sudo apt update
        sudo apt install git git-lfs
        ```

3. Install git-lfs hooks:

    ```sh
    git lfs install
    ```

</details>

### 1. Download Source

1. Open a terminal/PowerShell and navigate to the location where you would like to download the project
2. Clone this repository by clicking the **Code** button in the upper right and selecting either "Clone with SSH" or "Clone with HTTPS" to copy the repo URL, then run:

    ```shell
    git clone git@gitlab.msu.edu:ece-lemma/public/xnft/xnft.git
    ```

    > [!warning]
    > Update clone URL once project is public:
    > https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft.git

3. Enter into the `xnft` directory

    ```shell
    cd xnft
    ```

> [!Note]
> The SSH option will use your SSH keys allowing for more convenient passwordless authentication if your ssh-agent is properly configured.

### 2. Download Test Data (Optional)

Optional test data is stored in a secondary **[`xnft-data`](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft-data)** repository included as a git submodule in this project.  Note that these archives contain sevaral gigabytes of data and are thus not downloaded by default.

To pull the datasets, run:

1. Pull the file pointers:

   On macOS/Linux:

   ```shell
   GIT_LFS_SKIP_SMUDGE=1 git submodule update --init --recursive
   ```

   On Windows (PowerShell):

   ```shell
   $env:GIT_LFS_SKIP_SMUDGE = '1'; git submodule update --init --recursive
   ```

2. Download the files

   ```shell
   git submodule update --init --recursive
   ```

This will download datasets in to the `data/...` folders.

### 3. Install and Run

To quickly install the environment to run _xNFT_, run:

```shell
pixi run xnft
```

This will install all packages necessary into the `default` Pixi environment, then run _xNFT_ in the environment.
> [!NOTE]
> On the first run of `xnft` it may take some time to open as packages are compiled to Python bytecode. These compiled packages will be cached and it will open and run much faster on subsequent launches.

## Build Distributable Package (Optional)

> [!note]
> Due to licensing concerns, a redistributable package with embedded third-party dependencies is not provided by the CI.  Users may create this for personal use via the provided scripts if desired.

> [!note]
> Building a standalone redistributable pacakge currenly only works for macOS (`.app`) and Windows (`.exe`). Currently, an issue exists with packaging some `.so` files in the Linux build path.

The `pixi.toml` provides packaging tasks to generate a standalone executable.  Note that this can only generate a target package to run on the same OS/architecture as the build platform, e.g., macOS/arm64, Windows-11/x86, etc.

To build simply run:

```shell
pixi run build-exe
```

Once the build completes, the package will be located in the `dist` folder.