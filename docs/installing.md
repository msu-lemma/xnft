# Installing _xNFT_

## Table of Contents

1. [Install From Python Package Index (PyPI) (Recommended)](#1-install-from-python-package-index-pypi-recommended)
2. [Install From Development Package](#2-install-from-development-package)
3. [Install From Source](#3-installing-from-source)
4. [Build Redistributable Package with Embedded Dependencies](#4-build-distributable-package)
5. [Download Test Data](#5-download-test-data-optional)

## 1. Install From Python Package Index (PyPI) (Recommended)

**Prerequesite:** To install xnft it's recommended to use `uv`. To install `uv` visit: https://docs.astral.sh/uv/getting-started/installation/. It may be necessary to close and re-open your terminal after installing `uv`.

### 1.1 Install _xNFT_

To install _xNFT_ from PyPI using `uv` run:

```shell
uv tool install xnft
```

To run _xNFT_ simply run:

```shell
xnft
```

### 1.2 Install Extensions (Optional)

To install optional field loaders, e.g., `xnft-lemma-scanner` field loader, run:

```shell
uv tool install xnft --with xnft-lemma-scanner
```

Further extensions from PyPI or `.whl` files can be added after the `--with` flags if desired as well.

### 1.3 Download Test Data (Optional)

To download test data for evaluating _xNFT_ see **[Download Test Data](#5-download-test-data-optional)**

## 2. Install From Development Package

Installing from a packaged source is recommended for _xNFT_ users. The CI pipeline publishes pre-built packages for every commit which may be downloaded and installed, described in this section.

To install the latest tagged version, see [Install From Python Package Index (PyPI)](#1-install-from-python-package-index-pypi-recommended). For developers, see [Installing from Source](3-installing-from-source).

### 2.1 Download _xNFT_

The CI pipeline produces packaged versions of _xNFT_ are provided in `.conda` (conda/pixi format) and `.whl` (pip format) which can be found at the links in the following section.

Two package versions are available:

- **[Latest Release](https://gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases/permalink/latest)**

    Any release version can be downloaded from the [Releases page](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases).   Each release contains `.conda` and `.whl` artifacts to install.

- **[Development Packages](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/packages/)**

    Development packages are generated from the `main` branch which contain the latest features and bug fixes but may be less stable than the [Release packages](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/releases). Each build contains `.conda` and `.whl` artifacts to install.

### 2.2 Install _xNFT_

Once the desired xNFT version has been downloaded, the package may be installed.

The two supported methods of installation are using **[pixi](https://pixi.prefix.dev/latest/)** or **[uv](https://docs.astral.sh/uv/)**.

- **Install via uv  (recommended)**

    **Prerequesite:** Install uv: https://docs.astral.sh/uv/getting-started/installation/. It may be necessary to close and re-open your terminal after installing `uv`.

    To install _xNFT_ using `uv`, first download the `.whl` file, then run

    ```shell
    uv tool install --python 3.14 xnft-<version>-py3-none-any.whl
    ```

    Replace `<version>` with the version in the file name downloaded from the link above.

    Once installed, _xNFT_ may be run from the terminal simply as:

    ```shell
    xnft
    ```

    > [!NOTE]
    >
    > Extensions from PyPI or `.whl` files can be appended to the install command using the `--with` flag, e.g.:
    >
    > ```shell
    > uv tool install --python 3.14 xnft-<version>-py3-none-any.whl --with xnft-lemma-scanner
    > ```

- **Install via pixi**

    **Prerequesite:** Install pixi: https://pixi.prefix.dev/latest/installation/. It may be necessary to close and re-open your terminal after installing `uv`.

    To install the _xNFT_ using pixi, first download the `.conda` file, then run

    ```shell
    pixi global install -e xnft --path xnft-<version>.conda 
    ```

    Once installed, _xNFT_ may be run from the terminal simply as:

    ```shell
    xnft
    ```

    > [!NOTE]
    >
    > Extensions from `.conda` files can be appended to the install command using the `--with` flag, e.g.:
    >
    > ```shell
    > pixi global install -e xnft --path xnft-<version>.conda --with xnft-lemma-scanner-<version>.conda
    > ```

### 2.3 Download Test Data (Optional)

To download test data for evaluating _xNFT_ see **[Download Test Data](#5-download-test-data-optional)**

## 3. Installing From Source

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
2. Clone this repository by running:

    ```shell
    git clone https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft.git
    ```

3. Enter into the `xnft` directory

    ```shell
    cd xnft
    ```

### 2.2 Download Test Data (Optional)

Optional test data is stored in a secondary **[`xnft-data`](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft-data)** repository included as a git submodule in this project.  Note that these archives contain sevaral gigabytes of data and are thus not downloaded by default.

To pull the datasets, run:

1. Pull the file pointers:

   **On macOS/Linux:**

   ```shell
   GIT_LFS_SKIP_SMUDGE=1 git submodule update --init --recursive --checkout
   ```

   **On Windows (PowerShell):**

   ```shell
   $env:GIT_LFS_SKIP_SMUDGE = '1'; git submodule update --init --recursive --checkout
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

## 4. Build Distributable Package

> [!note]
> Due to licensing concerns, a redistributable package with embedded third-party dependencies is not provided by the CI.  Users may create this for personal use via the provided scripts if desired.

> [!note]
> Building a standalone redistributable pacakge currenly only works for macOS (`.app`) and Windows (`.exe`). Currently, an issue exists with packaging some `.so` files in the Linux build path.

First, follow the [Installing From Source](#3-installing-from-source) instructions above.

The `pixi.toml` provides packaging tasks to generate a standalone executable.  Note that this can only generate a target package to run on the same OS/architecture as the build platform, e.g., macOS/arm64, Windows-11/x86, etc.

To build simply run:

```shell
pixi run build-exe
```

Once the build completes, the package will be located in the `dist` folder.

## 5. Download Test Data (Optional)

Test data for evaluating _xNFT_ can be found in the **[_xNFT_ Data](https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft-data)** repository.  

A zip of the entire data repository can be downloaded by selecting the `Code` drop-down button in the upper-right corner, then selecting one of the file options below "Download Source Code".  Note that this may be several gigabytes.

Altnernatively, individual test files may be downloaded by navigating the `near_field` and `far_field` folders directly.