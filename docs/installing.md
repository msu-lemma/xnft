# Installing _xNFT_

## Table of Contents

1. [Install via Package](#1-install-via-package)
2. [Install From Source](#2-installing-from-source)
3. [Build Redistributable Package with Embedded Dependencies](#3-build-distributable-package)

## 1. Install via Package

### 1.1 Download _xNFT_

> [!NOTE]
> Installation via PyPI and conda-forge are planned but not yet supported.

Packaged versions of _xNFT_ are provided in `.conda` (conda/pixi format) and `.whl` (pip format) which can be found at the links in the following section.

Two package versions are available:

- **[Latest Release](https://gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases/permalink/latest)**

    Any release version can be downloaded from the [Releases page](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases).   Each release contains `.conda` and `.whl` artifacts to install.

- **[Development Packages](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/packages/)**

    Development packages are generated from the `main` branch which contain the latest features and bug fixes but may be less stable than the [Release packages](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases).. Each build contains `.conda` and `.whl` artifacts to install.

    The latest development wheel package may also be installed using `uv` directly from the MSU GitLab PyPI registry by running:

    ```shell
    uv tool install xnft --index-url https://www.gitlab.msu.edu/api/v4/projects/28094/packages/pypi/simple
    ```

> [!note]
> When using PyPI, it is recommended to use an environment manager such as [conda](https://docs.conda.io/projects/conda/en/stable/), [pixi](https://pixi.prefix.dev/latest/), [venv](https://docs.python.org/3/library/venv.html), or [pipenv](https://pipenv.pypa.io/en/latest/) to minimize package conflicts with system Python installs.

### 1.2 Install _xNFT_

Once the desired xNFT version has been downloaded from [Package Sources](#11-package-sources), the package may be installed.

#### Install via pixi

**Prerequesite:** Install pixi: https://pixi.prefix.dev/latest/installation/. It may be necessary to close and re-open your terminal after installing `uv`.

To install the conda package using pixi

```shell
pixi global install --path xnft-<version>.conda 
```

Once installed, _xNFT_ may be run from the terminal simply as:

```shell
xnft
```

#### Install via uv

**Prerequesite:** Install uv: https://docs.astral.sh/uv/getting-started/installation/. It may be necessary to close and re-open your terminal after installing `uv`.

To install the downloaded wheel run

```shell
uv tool install --python 3.14 xnft-<version>-py3-none-any.whl
```

Replace `<version>` with the version in the file name downloaded from the link above.

Once installed, _xNFT_ may be run from the terminal simply as:

```shell
xnft
```

## 2. Installing From Source

Installing from source is required to develop or package _xNFT_. To install _xNFT_ from source, it is recommended to use Pixi to manage the environment (<https://pixi.prefix.dev/latest/>).

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

### 2.1 Download Source

1. Open a terminal/PowerShell and navigate to the location where you would like to download the project
2. Clone this repository by clicking the **Code** button in the upper right and selecting either "Clone with SSH" or "Clone with HTTPS" to copy the repo URL, then run:

    ```shell
    git clone git@gitlab.msu.edu:ece-lemma/public/xnft/xnft.git
    ```

    > [!WARNING]
    >
    > **TODO: Update clone URL once project is public:
    > https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft.git**

3. Enter into the `xnft` directory

    ```shell
    cd xnft
    ```

> [!Note]
> The SSH option will use your SSH keys allowing for more convenient passwordless authentication if your ssh-agent is properly configured.

### 2.2 Download Test Data (Optional)

Optional test data is stored in a secondary **[`xnft-data`](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft-data)** repository included as a git submodule in this project.  Note that these archives contain sevaral gigabytes of data and are thus not downloaded by default.

To pull the datasets, run:

1. Pull the file pointers:

   **On macOS/Linux:**

   ```shell
   GIT_LFS_SKIP_SMUDGE=1 git submodule update --init --recursive
   ```

   **On Windows (PowerShell):**

   ```shell
   $env:GIT_LFS_SKIP_SMUDGE = '1'; git submodule update --init --recursive
   ```

2. Download the files

   ```shell
   git submodule foreach --recursive 'git lfs pull'
   ```

This will download datasets in to the `data/...` folders.

### 2.3 Install and Run

To quickly install the environment to run _xNFT_, run:

```shell
pixi run xnft
```

This will install all packages necessary into the `default` Pixi environment, then run _xNFT_ in the environment.
> [!NOTE]
> On the first run of `xnft` it may take some time to open as packages are compiled to Python bytecode. These compiled packages will be cached and it will open and run much faster on subsequent launches.

## 3. Build Distributable Package

> [!note]
> Due to licensing concerns, a redistributable package with embedded third-party dependencies is not provided by the CI.  Users may create this for personal use via the provided scripts if desired.

> [!note]
> Building a standalone redistributable pacakge currenly only works for macOS (`.app`) and Windows (`.exe`). Currently, an issue exists with packaging some `.so` files in the Linux build path.

First, follow the [Installing From Source](#2-installing-from-source) instructions above.

The `pixi.toml` provides packaging tasks to generate a standalone executable.  Note that this can only generate a target package to run on the same OS/architecture as the build platform, e.g., macOS/arm64, Windows-11/x86, etc.

To build simply run:

```shell
pixi run build-exe
```

Once the build completes, the package will be located in the `dist` folder.