[![Website](https://img.shields.io/badge/sqr--086-lsst.io-brightgreen.svg)](https://sqr-086.lsst.io)
[![CI](https://github.com/lsst-sqre/sqr-086/actions/workflows/ci.yaml/badge.svg)](https://github.com/lsst-sqre/sqr-086/actions/workflows/ci.yaml)

# A data documentation deep linking service with IVOA DataLink

## SQR-086

LSST users retrieve data through VO services, either directly or through clients like the Rubin Science Platform's Portal. IVOA provides a DataLink specification that allows datasets to express relationships with other resources, such as related datasets. This technote outlines a method for using DataLink to also link into the documentation for data, both at the table and column level. With this standards-based approach, clients like the Portal can show descriptions and links to documentation from their user infraces.

**Links:**

- Publication URL: https://sqr-086.lsst.io
- Alternative editions: https://sqr-086.lsst.io/v
- GitHub repository: https://github.com/lsst-sqre/sqr-086
- Build system: https://github.com/lsst-sqre/sqr-086/actions/


## Build this technical note

You can clone this repository and build the technote locally if your system has Python 3.11 or later:

.. code-block:: bash

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
