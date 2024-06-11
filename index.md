# Deep linking to data documentation with IVOA DataLink

```{abstract}
When presenting LSST data through VO services, we want to annotate that data with links to documentation, such as the table and column descriptions in data release documentation sites hosted on `lsst.io`.
This technote describes a system where we implement a linking service that uses the IVOA DataLink standard to provide links to table and column documentation.
This link service, which resides in the Rubin Science Platform (RSP), is called by TAP schema queries.
In turn, the link service queries Ook, Rubin Observatory's documentation metadata service that indexes the link inventories of documentation sites.
These link inventories are prepared and included with Sphinx documentation builds using Sphinx extensions provided by the Documenteer package.
With this standards-based approach, clients like the Portal can show descriptions and links to documentation from their user interfaces.
```

## High level overview

This overview traces the system's component architecture from the end-user's perspective through to the intention of the documentation author.

```{diagrams} overview_diagram.py
:filename: overview-diagram.png
```

Consider a Rubin Science Platform user who is working in the Portal to query and view LSST data.[^agnostic]
The Firefly-based Portal shows information about tables and columns by making queries against the [TAP][tap] schema.
The LSST TAP schemas are annotated with [DataLink][datalink] service descriptors points to a link service, also hosted in the RSP, that provides links to entities like tables and columns in an LSST data release.
These service descriptors are added to the TAP schema through definition files in [sdm_schemas][sdm_schemas], which is managed through [Felis][felis].
The service descriptors specify access URLs, including query parameters, to a link endpoint provided by another RSP service.
In the RSP, the [datalinker][datalinker] Python project provides a link service that can be extended for this application.
The link endpoint, through the datalinker service, operates in the RSP so that it can be aware of what data is available in that RSP, and can make any last-mile transformations to the links, including adding RSP-specific links.
See [](#datalinker-service).

[^agnostic]: Although we use the Portal as the example, and also as the driving use case, by adopting the IVOA DataLink standard, other VO clients can also get documentation links.

Most documentation links will be provided through documentation sites hosted outside the Rubin Science Platform on `lsst.io`, which is managed by the LSST the Docs ({sqr}`006`) static documentation site platform.
So that the link service in the RSP doesn't have to be aware in detail of these documentation sites, and also so that other data facilities can mix in other documentation sources for their RSP deployments, we propose that the link service also acts as a proxy to a link provider that lives closer to the documentation domain.

The [Ook][ook] documentation librarian service, which is hosted in the Roundtable internal services Kubernetes cluster, already indexes Rubin documentation sites.
For this application, Ook provides a new links API that provides deep links into the documentation sites for specific entities like data release data and column documentation.
See [](#ook-link-service).

To associate semantic meaning with the deep link anchors in documentation, Ook will interface specifically with the [Intersphinx][intersphinx] object inventory files that Sphinx projects publish to their `/objects.inv` paths.
These object inventories associate hyperlink targets to all [domain][domain] entities in a Sphinx project.
To make meaningful domain entities, we will introduce a custom [Sphinx domain][domain] for Rubin Observatory documentation to mark up data release reference documentation and related concepts.
See [](#link-inventories).

Overall this system provides a standards-based approach both for linking to documentation with VO clients and for authoring documentation with Sphinx.

(link-inventories)=
## Link inventories in Sphinx documentation

In this architecture, TAP tables and columns are annotated with links to Rubin documentation, such as a data release documentation site.
This documentation is built with the [Sphinx][Sphinx]/[Documenteer][Documenteer] toolchain.
To accomplish this, we will build upon the core Sphinx technologies of [domains][domain] and [Intersphinx][intersphinx] to structure and annotate Rubin data release documentation that it is cross-referenceable with machine-readable link inventories.

(rubin-domain)=
### Marking up documentation with link anchors

In the documentation source, we will use custom extensions (reStructuredText roles and directives) provided through [Documenteer][Documenteer] to annotate specific pages and sections as documenting a table or column.
These Sphinx extensions will be part of a Rubin Observatory [Sphinx *domain*][domain].
Sphinx domains are collections of directives that allow writers to document specific types of entities and cross reference those.
Sphinx includes built-in domains for Python, C++, and other programming languages, which is how Sphinx API references are built.

An example of how a table and column might be documented in a Sphinx project:

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
Complementary Sphinx roles let writers cross-reference these entities in other parts of the documentation project (or even in other Sphinx projects with [Intersphinx][intersphinx]):

```{code-block} rst
See the :rubin:table:`Visit` table for more information.

The filter for the observation is given
in the :rubin:column:`physical_filter` column.
```

### Publishing link inventories from Sphinx documentation

By integrating with the Sphinx domains API, the inventory of all Rubin documentation entities, like data release tables and columns, is automatically part of the [Intersphinx][intersphinx] object inventory.
Intersphinx publishes this inventory as a file (`objects.inv`) that is hosted alongside the HTML documentation site.
Although the `objects.inv` format is somewhat opaque, Sphinx provides a Python API for reading it.
We will use that API in the [Ook link service](#ook-link-service).

(ook-link-service)=
## The Ook link service

[Ook][Ook] is an existing SQuaRE service that serves as a documentation librarian.
Ook's existing role is to index documents and populate the Algolia full-text search database that powers the Rubin Observatory documentation search at www.lsst.io.
We propose to extend Ook to also index the link inventories (generally speaking the `objects.inv` Intersphinx inventory files).
The Ook link service would sync these inventories into a Postgres database and then provide a REST API for querying the inventories.

```{mermaid}
flowchart LR
  objadapter[Object Inventory Adapter]
  objects["dr1.lsst.io/objects.inv"]
  documenteer[Documenteer Sphinx Domain]
  service[Ook Link Service]
  db[Postgres Database]
  api[Ook Link API]
  vo[VO data linking service]
  vo --> api
  api --> service
  service --> objadapter
  objadapter --> objects
  documenteer --> objects
  service --> db
```

Ook's link API would be structured around the different Sphinx domains, including the Rubin domain for linking to Rubin data products and other entities.
For example, to get the link to a column's documentation:

```{code-block}
GET /ook/links/domain/rubin/dr/dp02/tables/visit/columns/physical_filter
```

With the same technology, we can provide a generic API for other Sphinx domains:

```{code-block}
GET /ook/links/domain/python/module/lsst.afw.table
```

Internally, the Ook link service would follow a process like this:

1. Based on a manual trigger, or Kafka message from the LTD documentation publishing system, Ook would trigger an update of the project's link inventory. This trigger is similar to how Ook's Algolia indexding for a documentation project is triggered.
2. Ook interface to Sphinx's `objects.inv` file format downloads and read the inventory file.
3. The Ook link service upserts the entities from the inventory into a Postgres database. Ook maintains the schemas for these object inventory tables given that the Ook API also needs is aware of what Sphinx domains it publishes.
4. The Ook link service provides a REST API for querying the link inventory.

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

So long as the names for the entities and URL template variables are well known, this root endpoint can provide a discovery and auto-configuration layer for clients.

### Structure of the entity link API

The entity linking APIs let a client get the links for a specific entity based on the URL structure.

```{code-block}
GET /ook/links/domain/rubin/dr/dr1/tables/visit/columns/physical_filter
```

The JSON response for a specific entity would include, at a minimum, the URL to the documentation page and anchor for that entity.

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

### Structure of the entity collections API

A client may need bulk access to links to a collection of entities, without needing to make a large number of HTTP requests.
For example, a client may need all columns in a table, or all tables in a data release.
For these cases, the collections APIs can provide an array of entities and their links:

```{code-block}
GET /ook/links/domain/rubin/dr/dr1/tables/visit/columns
```

With a query string syntax, we could let the client get a subset of the collection.
for example, all columns that start with a prefix:

```{code-block}
GET /ook/links/domain/rubin/dr/dr1/tables/visit/columns?prefix=visit_
```

The response includes both a data field and a separate pagination field:

```{code-block} json
{
  "data": [
    {
      "name": "physical_filter",
      "links": [
        {
          "url": "https://dr1.lsst.io/reference/tables/visit#physical_filter",
          "kind": "documentation",
          "source_title": "Data Release 1 Documentation"
        }
      ]
    },
    {
      "name": "visit_id",
      "links": [
        {
          "url": "https://dr1.lsst.io/reference/tables/visit#visit_id",
          "kind": "documentation",
          "source_title": "Data Release 1 Documentation"
        }
      ]
    }
  ],
  "pagination": {
    "previous": "/ook/links/domain/rubin/dr/dr1/tables/visit/columns?before=physical_filter"
    "next": "/ook/links/domain/rubin/dr/dr1/tables/visit/columns?after=visit_id"
  }
}
```

This response schema features cursor-based pagination.

#### Including child entities?

Many entities in the [Rubin domain](#rubin-domain) described here are natural hierachical.
A data release contains tables, and those tables contain columns.
It could be useful to include child entities in the response for a parent entity (essentially embedding the collections API for the child entitities in the response for the parent entity).
If we do this, we should study how other APIs handle pagination in these types of responses.

(datalinker-service)=
## Implementation of a VO data linking endpoint

TK

[Sphinx]: https://www.sphinx-doc.org/
[Documenteer]: https://documenteer.lsst.io/
[Intersphinx]: https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
[Ook]: https://github.com/lsst-sqre/ook
[sdm_schemas]: https://github.com/lsst/sdm_schemas
[felis]: https://github.com/lsst-dm/felis
[domain]: https://www.sphinx-doc.org/en/master/extdev/domainapi.html
[datalink]: https://www.ivoa.net/documents/DataLink/
[tap]: https://www.ivoa.net/documents/TAP/
[datalinker]: https://github.com/lsst-sqre/datalinker
