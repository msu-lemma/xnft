# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Stable serialization scheme using zip file to hold pickled attributes and hdf5 data in one container.
- Save/load project moved to separate thread; added UI indications to user to show save/load in progress.
- Data nodes can now be deleted
- Data nodes can now be renamed

### Fixed

- Projects with reports/plots can now be saved
- `.xnft` file schema now stable (software updates should not break existing data files)
- Line Plot now works for plotting any field component

[unreleased]: https://www.gitlab.msu.edu/ece-lemma/public/xnft/xnft/-/compare/v0.1.0b2...HEAD
