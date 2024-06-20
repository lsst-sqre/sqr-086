[![Website](https://img.shields.io/badge/sqr--086-lsst.io-brightgreen.svg)](https://sqr-086.lsst.io)
[![CI](https://github.com/lsst-sqre/sqr-086/actions/workflows/ci.yaml/badge.svg)](https://github.com/lsst-sqre/sqr-086/actions/workflows/ci.yaml)

# Deep linking to data documentation with IVOA DataLink

## SQR-086

When presenting LSST data through VO services, we want to annotate that data with links to documentation, such as the table and column descriptions in data release documentation sites hosted on `lsst.io`.
This technote describes a system where we implement a linking service that uses the IVOA DataLink standard to provide links to table and column documentation.
This link service, which resides in the Rubin Science Platform (RSP), is called by TAP schema queries.
In turn, the link service queries Ook, Rubin Observatory's documentation metadata service that indexes the link inventories of documentation sites.
These link inventories are prepared and included with Sphinx documentation builds using Sphinx extensions provided by the Documenteer package.
With this standards-based approach, clients like the Portal can show descriptions and links to documentation from their user interfaces.

**Links:**

- Publication URL: https://sqr-086.lsst.io
- Alternative editions: https://sqr-086.lsst.io/v
- GitHub repository: https://github.com/lsst-sqre/sqr-086
- Build system: https://github.com/lsst-sqre/sqr-086/actions/

## Build this technical note

You can clone this repository and build the technote locally if your system has Python 3.11 or later:

```sh
git clone https://github.com/lsst-sqre/sqr-086
cd sqr-086
make init
make html
```

Repeat the `make html` command to rebuild the technote after making changes.
If you need to delete any intermediate files for a clean build, run `make clean`.

The built technote is located at `_build/html/index.html`.

## Publishing changes to the web

This technote is published to https://sqr-086.lsst.io whenever you push changes to the `main` branch on GitHub.
When you push changes to a another branch, a preview of the technote is published to https://sqr-086.lsst.io/v.

## Editing this technical note

The main content of this technote is in `index.md` (a Markdown file parsed as [CommonMark/MyST](https://myst-parser.readthedocs.io/en/latest/index.html)).
Metadata and configuration is in the `technote.toml` file.
For guidance on creating content and information about specifying metadata and configuration, see the Documenteer documentation: https://documenteer.lsst.io/technotes.
