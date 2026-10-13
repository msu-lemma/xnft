# xNFT: An Open Near-Field Antenna Measurement Software Suite

> [!CAUTION] ⚠️ xNFT is in active development (Beta)
> xNFT is in active development. In beta, user interfaces and APIs may continue to change. For the most stable operation, use the latest tagged release. For the most up-to-date features and bug fixes, consider using `main` branch.

## What is xNFT?

**xNFT** is a cross-platform, high-performance, general purpose antenna measurement and analysis software tool, primarily focusing on near-to-far field transformations (NFTs), permissively distributed under the MIT license.

![xnft Screenshot](docs/source/assets/xnft_screenshot.png)
> Screenshot of xNFT running on macOS.  Measurements show an NSI-MI ANT-SGH-26.5-40 standard gain horn at 40 GHz collected using the LEmmA planar near-field scanner.

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
2. Install `git`. This may be installed via the OS package manager or pixi. Choose **_one_** option below:
    - **Winget (Windows):** In any "PowerShell" run:

        ```PowerShell
        winget install --id Git.Git -e --source winget
        ```

    - **Pixi (macOS or Linux):** in a terminal run:

        ```sh
        pixi global install --environment git --expose git git-lfs
        ```

        This will add the `git` and `git-lfs` executables to a global directory (typically in your home folder) and add the `git` executable to your terminal's search path.

    - **Homebrew (macOS):** In terminal install via xcode-select or [Homebrew](https://brew.sh):

        ```sh
        xcode-select --install
        # or
        brew install git
        ```

    - **APT (Ubuntu/Debian):** In terminal install via apt:

        ```sh
        apt install git
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
git submodule init && git submodule update --recursive
```

This will download datasets in to the `data/...` folders.

## Documentation

> [!NOTE]
> The documentation currently only contains API docs. Further user/theory documentation is in progress.

#### Pre-built Docs

The latest automated docs build can be downloaded here: [**Download Latest Documentation**](https://gitlab.msu.edu/api/v4/projects/28094/jobs/artifacts/main/download?job=docs-build-job)

Once downloaded, unzip the archive and navigate to **`build/html/index.html`** to access the documentation.

#### Local Docs Generation

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
