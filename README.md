# xNFT: An Open Near-Field Antenna Measurement Software Suite

> [!CAUTION] ⚠️ xNFT is in active development (Beta)
> xNFT is in active development. In beta, user interfaces and APIs may continue to change. For the most stable operation, use the latest tagged release. For the most up-to-date features and bug fixes, consider using `main` branch.

| | |
| ------ | ------ |
| Testing | [![Pipeline Status](https://gitlab.msu.edu/delta/internal/libs/python-packages/delta-python-package/badges/main/pipeline.svg?ignore_skipped=true&job=test-job)](https://gitlab.msu.edu/delta/internal/libs/python-packages/delta-python-package/-/pipelines) ![Test Coverage](https://gitlab.msu.edu/delta/internal/libs/python-packages/delta-python-package/badges/main/coverage.svg) |
| Package | [![Latest Release](/../../badges/release.svg)](/../../releases) |
| Meta | ![License: MIT](https://img.shields.io/badge/License-MIT-green) |

## What is xNFT?

**xNFT** is a cross-platform, high-performance, general purpose antenna measurement and analysis software tool, primarily focusing on near-to-far field transformations (NFTs), permissively distributed under the MIT license.

![xnft Screenshot](docs/source/assets/xnft_screenshot.png)
> Screenshot of xNFT running on macOS.  Measurements show an NSI-MI ANT-SGH-26.5-40 standard gain horn at 40 GHz collected using the LEmmA planar near-field scanner.

## Known Issues

xNFT is in active development and has several known limitations that are currently being addressed.  A summary of the high-impact issues are included in the [Work Items](https://www.gitlab.msu.edu/ece-lemma/internal/xnft-antenna-measurement-software/xnft/-/work_items?sort=created_date&state=opened&or%5Blabel_name%5D%5B%5D=Impact%3A%3AHigh&or%5Blabel_name%5D%5B%5D=Priority%3A%3ACritical&or%5Blabel_name%5D%5B%5D=Priority%3A%3AHigh&not%5Blabel_name%5D%5B%5D=docs&first_page_size=100).

</details>

## Requirements

xNFT is designed to run on a wide range of operating systems and architectures.  A list of system configurations designed to be compatible is included below. Other configurations may work, but are not currently considered supported configurations.

### xNFT Design System Compatability Matrix

| Operating System | Versions          | Architectures    |
| ---------------- | ----------------- | ---------------- |
| macOS            | >= 15.0 (Sequoia) | arm-64, x86-64   |
| Linux            | ——                | x86-64, aarch64  |
| Windows          | 10, 11            | x86-64           |

### Validated Configurations

<details>
<summary>(Click to view table)</summary>

| Operating System | Versions         | Architecture |
| ---------------- | ---------------- | ------------ |
| macOS            | 26 (Tahoe)       | arm-64       |
|                  | 27 (Golden Gate) | arm-64       |
| Alma Linux       | 8.10, 9.6, 9.8   | x86-64       |
| Ubuntu           | 26.04            | aarch64      |
| Windows          | 11               | x86-64       |

</details>

## Installation

### From Source

For the latest features and bug fixes, install from source.

> [!NOTE]
> The development environment uses the Pixi package manager (<https://pixi.prefix.dev/latest/>) and git (<https://git-scm.com>) to manage the envrionment and source code. It may be helpful to have a basic understanding of Pixi and git to install and use this software.

> [!WARNING]
> Installing from the `main` branch may be unstable.  For the most stable operation, install the latest release.

<details>
<summary>
<h3>Prerequisites</h3> (Click to view)
</summary>

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

#### Download

1. Open a terminal/PowerShell and navigate to the location where you would like to download the project
2. Clone this repository by clicking the **Code** button in the upper right and selecting either "Clone with SSH" or "Clone with HTTPS" to copy the repo URL, then run:

    ```shell
    git clone <copied-url>
    ```

> [!Note]
> The SSH option will use your SSH keys allowing for more convenient passwordless authentication if your ssh-agent is properly configured.

#### Install and Run

To quickly install the environment to run xNFT, run:

```shell
pixi run xnft
```

This will install all packages necessary into the `default` Pixi environment, then run xNFT in the environment.
> [!NOTE]
> On the first run of `xnft` it may take some time to open as packages are compiled to Python bytecode. These compiled packages will be cached and it will open and run much faster on subsequent launches.

#### Download Test Data (Optional)

Optional test data is stored in a secondary `xnft-data` repository included as a git submodule in this project.  Note that these archives contain sevaral gigabytes of data and are thus not downloaded by default.

To pull the datasets, run:

```sh
git submodule update --init --recursive
```

This will download datasets in to the `data/...` folders.

## Documentation

> [!NOTE]
> The documentation currently only contains API docs. Further user/theory documentation is in progress.

### Pre-built Docs

The latest automated docs build can be downloaded here: [**Download Latest Documentation**](https://gitlab.msu.edu/api/v4/projects/28094/jobs/artifacts/main/download?job=docs-build-job)

Once downloaded, unzip the archive and navigate to **`build/html/index.html`** to access the documentation.

### Local Docs Generation

To build all docs locally (PDF and HTML), run:

```shell
pixi run -e docs build-docs
```

If you do not have a LaTeX toolchain installed locally, the above command will fail. You can still build the HTML-only docs by running

```shell
pixi run -e docs build-html-docs
```

## License

Copyright 2026 Michigan State University. All rights reserved.

The original source code for this project is distributed under the MIT license. See [LICENSE](LICENSE).

This project depends on third-party libraries which are distributed separately and remain subject to their respective licenses.  For a complete list of runtime dependencies, see the `package.run-dependencies` section of the [`pixi.toml`](pixi.toml) file.

## Acknowledgement

This work was sponsored by the Air Force Research Laboratory (AFRL) under grant number FA87502510001. The views expressed are those of the authors and do not reﬂect the ofﬁcial policy or position of he Department of Defense or the U.S. Government
