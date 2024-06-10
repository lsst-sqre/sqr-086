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
To accomplish this, we will built upon the core Sphinx technologies of domains and Intersphinx.

### Marking up documentation with link anchors

In the documentation source, we will use custom extensions (reStructuredText roles and directives) provided through [Documenteer][Documenteer] to annotate specific pages and sections as documenting a table or column.
These Sphinx extensions will be part of a Rubin Observatory Sphinx *domain*.
Sphinx domains are collections of directives that allow writers to document specific types of entities and cross reference those.
Sphinx includes built-in domains for Python, C++, and other programming languages, which is how Sphinx API references are built.

An example of how a table and column might be documented in a a Sphinx project:

```{code-block} rst

.. :rubin:table: Visit
   :release: dp02_dc2_catalogs

Content about the ``Visit`` table goes here
for the DP0.2 DC2 catalogs.

.. :rubin:column:: physical_filter
   :table: Visit
   :release: dp02_dc2_catalogs

Content about the ``physical_filter`` column
goes here for the DP0.2 DC2 catalogs
and ``Visit`` table.
```

These custom directives (e.g., `:rubin:table:`, `:rubin:column:`) leave structured hyperlink anchors in the generated HTML output.
Complementary Sphinx roles let writer cross-reference these entities in other parts of the documentation project (or even in other Sphinx projects with Intersphinx):

```{code-block} rst
See the :rubin:table:`Visit` table for more information.

The filter for the observation is given in the :rubin:column:`physical_filter` column.
```

### Publishing link inventories from Sphinx documentation

By integrating with the Sphinx domains API, the inventory of all Rubin documentation entities, like data release tables and columns, is automatically part of the Intersphinx object inventory.
Intersphinx publishes this inventory as a file (`objects.inv`) that is hosted alongside the HTML documentation site.
Although the `objects.inv` format is somewhat opaque, Sphinx provides a Python API for reading it.
We will use that API in the [Ook link service](#ook-link-service).

(ook-link-service)=
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
