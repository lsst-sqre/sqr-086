# Deep linking to data documentation with IVOA DataLink

```{abstract}
When presenting LSST data through VO services, we want to annotate that data with links to documentation, such as the table and column descriptions in data release documentation sites hosted on `lsst.io`.
This technote describes a system where we implement a linking service that uses the IVOA DataLink standard to provide links to table and column documentation.
This link service, which resides in the Rubin Science Platform (RSP), is called by TAP schema queries.
In turn, the link service queries Ook, Rubin Observatory's documentation metadata service that indexes the link inventories of documentation sites.
These link inventories are prepared and included with Sphinx documentation builds using Sphinx extensions provided by the Documenteer package.
With this standards-based approach, clients like the Portal can show descriptions and links to documentation from their user interfaces.
```

## Link inventories in Sphinx documentation

In this architecture, TAP tables and columns are annotated with links to Rubin documentation, such as a data release documentation site.
This documentation is built with the [Sphinx][Sphinx]/[Documenteer][Documenteer] toolchain.

### Marking up documentation with link anchors

In the documentation source, we will use custom extensions (reStructuredText roles and directives) provided through [Documenteer][Documenteer] to annotate specific pages and sections as documenting a table or column.
For example:

```{code-block} rst

.. rubin-table: Visit
   :release: dp02_dc2_catalogs

Content about the ``Visit`` table goes here
for the DP0.2 DC2 catalogs.

.. rubin-column:: physical_filter
   :table: Visit
   :release: dp02_dc2_catalogs

Content about the ``physical_filter`` column
goes here for the DP0.2 DC2 catalogs
and ``Visit`` table.
```

These custom directives (e.g., `rubin-table`, `rubin-column`) will leave structured hyperlink anchors in place in the generated HTML output.
Documenteer would provide corresponding Sphinx roles that link to these anchors based on the semantics of data release, table, and column names.

Besides adding anchors for cross referencing, such extensions could also help to add structure and styling to the documentation, similar to how Python APIs are generated.

### Publishing link inventories from Sphinx documentation

During the Sphinx build process for a documentation site, the Documenteer Sphinx extensions will collect all documented tables and columns and generate a link inventory.
This inventory is serialized as a structured data file (ideally JSON) and available from a well-known path relative to the documentation root (e.g. `/rubin-links.json`).
This inventory file would be ingested by the Ook links service, which in turns would be queried by the RSP link service.

### Integrating with Sphinx domains and intersphinx

Sphinx provides two built-in mechanisms for creating custom directives and roles for cross-referencing in documentation: [domains](https://www.sphinx-doc.org/en/master/usage/domains/index.html) and [intersphinx][Intersphinx].

Sphinx domains are composed of directives for defining entities and roles that reference those.
Sphinx has built-in domains for many programming languages, and this is how Sphinx API references are built.
For example, the Python domain has directives for defining classes, functions, and modules, and roles for referencing those.

Intersphinx works with domains to provide a published object inventory (`/objects.inv`) that's typically used by other Sphinx projects to facilitate cross-referencing across projects.

The custom roles and extensions mentioned above, along with the published link inventory, could also be accomplished by creating a "Rubin" domain in Sphinx.
For providing a standards-based approach, leveraging Sphinx domains and intersphinx is a good idea.

The downsides of this approach are that Sphinx domains are less flexible than a fully custom set of extensions, and the `objects.inv` format is slightly opaque without using the Sphinx Python API.
The former could be mitigated by using the Rubin domain for linking, and creating additional custom for styling and structure.
The later issue could be mitigated by a documentation link service, provided by Ook, described next.

## The Ook link service

[Ook][Ook] is an existing SQuaRE service that serves as a documentation librarian.
Ook's existing role is to index documents and populate the Algolia full-text search database that powers the Rubin Observatory documentation search at www.lsst.io.
We propose to extend Ook to also index the link inventories (generally speaking the `objects.inv` Intersphinx inventory files and Rubin's custom link inventories if Sphinx domains aren't used).
The Ook link service would sync these inventories into a Postgres database and then provide a REST API for querying the inventories.

Ook's link API would be structured around the different Sphinx domains, including the Rubin domain for linking to Rubin data products and other entities.
For example, to get the link to a column's documentation:

```{code-block}
GET /ook/links/domain/rubin/dr/dp02/table/visit/column/physical_filter
```

With the same technology, we can provide a generic API for other Sphinx domains:

```{code-block}
GET /ook/links/domain/python/module/lsst.afw.table
```

### Discovery and URL templating

The root endpoints for each link domain would provide templated URLs for the different entities:

```{code-block}
GET /ook/links/domain/rubin
```

```{code-block} json
{
  "entities": {
    "data-release": "/ook/links/domain/rubin/dr/{release}",
    "table": "/ook/links/domain/rubin/dr/{release}/tables/{table}",
    "column": "/ook/links/domain/rubin/dr/{release}/tables/{table}/columns/{column}"
  },
  "collections": {
    "data-releases": "/ook/links/domain/rubin/dr",
    "tables": "/ook/links/domain/rubin/dr/{release}/tables",
    "columns": "/ook/links/domain/rubin/dr/{release}/tables/{table}/columns"
  }
}
```

### Structure of a link response

The JSON response for a specific entity would include, at a minimum, the URL to the documentation page and anchor for that entity.

```{code-block}
GET /ook/links/domain/rubin/dr/dr1/table/visit/column/physical_filter
```

```{code-block} json
{
  "links": [
    {
      "url": "https://dr1.lsst.io/reference/tables/visit#physical_filter",
      "kind": "documentation",
      "source_title": "Data Release 1 Documentation"
    }
  ]
}
```

These link responses should anticipate that multiple links might be associated with a single entity.
For one, the "pull" nature of the Ook link service means that multiple documentation sites might claim to document the same entity.
To help clients distinguish between multiple links, Ook can provide some context for the links (whether it is a documentation site, or a document/technote, or a tutorial notebook, etc.).
As well, Ook can provide the name of the site that hosts the link.

The response schema should also anticipate that some entities might not just be related to deep links into documentation, but might also be related to images or other datasets.
Besides the `link` field, the response could include a `blobs` field that provides URLs that a client can follow to download the data.


[Sphinx]: https://www.sphinx-doc.org/
[Documenteer]: https://documenteer.lsst.io/
[Intersphinx]: https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
[Ook]: https://github.com/lsst-sqre/ook
