# Deep linking to data documentation with IVOA DataLink

```{abstract}
When presenting LSST data through VO services, we want to annotate that data with links to documentation, such as the table and column descriptions in data release documentation sites hosted on `lsst.io`.
This technote describes a system where we implement a linking service that uses the IVOA DataLink standard to provide links to table and column documentation.
This link service, which resides in the Rubin Science Platform (RSP), is called by TAP schema queries.
In turn, the link service queries Ook, Rubin Observatory's documentation metadata service that indexes the link inventories of documentation sites.
These link inventories are prepared and included with Sphinx documentation builds using Sphinx extensions provided by the Documenteer package.
With this standards-based approach, clients like the Portal can show descriptions and links to data documentation from their user interfaces.
```

## High-level overview

This overview traces the system's component architecture from the end-user's perspective through to the intention of the documentation author.

```{rst-class} technote-wide-content
```

```{diagrams} overview_diagram.py
:filename: overview-diagram.png
```

Consider a Rubin Science Platform user who is working in the Portal to query and view LSST data.[^agnostic]
The Firefly-based Portal shows information about tables and columns by making queries against the [TAP][tap] schema.
The LSST TAP schemas are annotated with [DataLink][datalink] service descriptors pointing to link endpoints, also hosted in the RSP, that provide URLs to related entities like table and column descriptions in LSST data release documentation.
These service descriptors are added to the TAP schema through definition files in [sdm_schemas][sdm_schemas], which is managed through [Felis][felis].
The service descriptors specify access URLs, including query parameters, to link endpoints provided by another RSP service.
In the RSP, the [datalinker][datalinker] Python application provides a link service that can be extended for this application.
The link endpoints, through the datalinker service, operate in the RSP so that they can be aware of what data is available in that RSP and can make any last-mile transformations to the links, including adding RSP-specific links.
See [](#datalinker-service).

[^agnostic]: Although we use the Portal as the example, and also as the driving use case, by adopting the IVOA DataLink standard other VO clients can also get documentation links.

Most documentation links will point to documentation sites hosted outside the Rubin Science Platform on `lsst.io`, which is managed by the LSST the Docs ({sqr}`006`) static documentation site platform.
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

In the documentation source, we will use custom extensions (reStructuredText roles and directives) provided through [Documenteer][Documenteer] to annotate specific pages and sections as documenting a table or column in a data release.
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
## The Ook links service

[Ook][Ook] is an existing SQuaRE application that serves as a documentation librarian.
Ook's established role is to index documents and populate the Algolia full-text search database that powers the Rubin Observatory documentation search at www.lsst.io.
We propose to extend Ook to also index link inventories (for example the `objects.inv` Intersphinx inventory files of Sphinx projects, but generally any relevant and linkable documentation or information source).
The Ook link service would sync these inventories into a Postgres database and then provide a REST API for querying the inventories.

See {ref}`ook-links-api` discussion of the web API and {ref}`ook-database-model` for the database modeling.

```{rst-class} technote-wide-content
```

```{mermaid}
:zoom:

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

Internally, the Ook link service would follow a process like this:

1. Based on a manual trigger, or Kafka message from the LTD documentation publishing system, Ook would begin an ingest of the project's link inventory. This trigger is similar to how Ook's Algolia indexing for a documentation project is triggered.
2. Ook's interface to Sphinx `objects.inv` file format downloads and reads the inventory file.
3. The Ook link service upserts the entities from the inventory into a Postgres database. Ook maintains the schemas for these object inventory tables given that the Ook API also needs is aware of what Sphinx domains it publishes.
4. The Ook link service provides a REST API for querying the link inventory.

(ook-links-api)=
## The Ook links API

Ook's link API would be structured around the different information domains.
Some of these domains would map directly to the Sphinx/Intersphinx domains such as the Rubin domain for linking to Rubin data products and other entities.
For example, to get the links to a Science Data Model (SDM) column's documentation:

```{code-block}
:class: technote-wide-content
GET /ook/links/domains/sdm/schemas/dp02_dc2_catalogs/tables/Visit/columns/physical_filter
```

With the same technology, we can provide a generic API for other Sphinx domains:

```{code-block}
:class: technote-wide-content
GET /ook/links/domains/python/modules/lsst.afw.table
```

### Discovery and URL templating

The root endpoints for each link domain would provide templated URLs for the different link endpoints, categorized around links to specific entities, or a collection of entities:

```{code-block}
GET /ook/links/domains/sdm
```

```{code-block} json
:class: technote-wide-content

{
  "entities": {
    "schema": "/ook/links/domains/sdm/schemas/{schema}",
    "table": "/ook/links/domains/sdm/schemas/{schema}/tables/{table}",
    "column": "/ook/links/domains/sdm/schemas/{schema}/tables/{table}/columns/{column}"
  },
  "collections": {
    "schemas": "/ook/links/domains/sdm/schemas",
    "tables": "/ook/links/domains/sdm/schemas/{schema}/tables",
    "columns": "/ook/links/domains/sdm/schemas/{schema}/tables/{table}/columns"
  }
}
```

So long as the names for the entities and URL template variables are well known, this root endpoint can provide a discovery and auto-configuration layer for clients.

(ook-entity-link)=
### Structure of an entity link API

The entity linking APIs let a client get the links for a specific entity based on the URL structure:

```{code-block}
:class: technote-wide-content

GET /ook/links/domains/sdm/schemas/dr1/tables/Visit/columns/physical_filter
```

The JSON response for a specific entity is an array of links:

```{code-block} json
:class: technote-wide-content

[
  {
    "url": "https://dr1.lsst.io/reference/tables/Visit#physical_filter",
    "type": "schema_browser",
    "source_title": "physical_filter column",
    "source_collection_title": "Data Release 1 Documentation"
  }
]
```

The link responses anticipates that multiple links might be associated with a single entity.
For one, the "pull" nature of the Ook link service means that multiple documentation sites might claim to document the same entity.
To help clients distinguish between multiple links, Ook can provide some context for the links (whether it is a documentation site, or a document/technote, or a tutorial notebook, etc.).
As well, Ook can provide the name of the site that hosts the link.

(ook-collection-link-api)=
### Structure of the entity collections API

A client may need bulk access to links for a collection of entities without needing to make a large number of HTTP requests.
For example, a client may need all columns in a table, or all tables in a data release.
For these cases, the collections APIs can provide an array of entities and their links:

```{code-block}
:class: technote-wide-content

GET /ook/links/domains/sdm/schemas/dr1/tables/Object/columns
```

With a query string syntax, we could let the client get a subset of the collection.
For example, all columns that start with a prefix:

```{code-block}
:class: technote-wide-content

GET /ook/links/domains/sdm/schemas/dr1/tables/Object/columns?prefix=shape_
```

The response for collections is an array of entities, and each entity has an array of links like in the the {ref}`entity link API <ook-entity-link>`:

```{code-block} json
:class: technote-wide-content

[
  {
    "schema_name": "dr1",
    "table_name": "Object",
    "column_name": "shape_flag",
    "links": [
      {
        "url": "https://dr1.lsst.io/reference/tables/Object#shape_flag",
        "type": "schema_browser",
        "source_title": "shape_flag column",
        "source_collection_title": "Data Release 1 Documentation"
      }
    ]
  },
  {
    "schema_name": "dr1",
    "table_name": "Object",
    "column_name": "shape_xx",
    "links": [
      {
        "url": "https://dr1.lsst.io/reference/tables/Object#shape_xx",
        "type": "schema_browser",
        "source_title": "shape_xx column",
        "source_collection_title": "Data Release 1 Documentation"
      }
    ]
  },
  {
    "schema_name": "dr1",
    "table_name": "Object",
    "column_name": "shape_xy",
    "links": [
      {
        "url": "https://dr1.lsst.io/reference/tables/Object#shape_xy",
        "type": "schema_browser",
        "source_title": "shape_xy column",
        "source_collection_title": "Data Release 1 Documentation"
      }
    ]
  },
]
```

```{note}
Many entities in the [Rubin domain](#rubin-domain) described here are naturally hierarchical.
A data release's schema contains tables, and those tables contain columns.
It could be useful to include child entities in the response for a parent entity (essentially embedding the collections API for the child entities in the response for the parent entity).
If we do this, we should study how other APIs handle pagination in these types of responses.
```

(ook-database-model)=
## Ook's database model

Ook's [link service](#ook-link-service) is backed by a Postgres datastore.
See {numref}`database-schema` for a visualization of the database schema.

```{rst-class} technote-wide-content
```

```{mermaid} database.mmd
:name: database-schema
:zoom:
:caption: Ook database schema that backs the Link Service.
```

### The links table

All links are stored in a common table, `links`.
These links have a website URL, a title, a type, and information about the documentation collection that they're part of.

The `type` field is a controlled vocabulary of resource content types, which may include `guide`, `tutorial`, `schema_browser`, `document`, and so on.
This field helps clients understand what kind of resource they're linking to.

The `source_collection_title` field is the title of the website the link is part of.
For example, a links to a schema in the DP1 data release documentation would have a `source_collection_title` of "LSST Data Release 1 Documentation."
With this generality, any type of link can be stored in this `links` table, whether is is a link to a section in a document, a link to a method in a Python API reference, or a link to a column in a schema browser.

### Link subtypes

The Ook Links API demands that links have a structured context.
For example, consider the SDM columns links endpoint:

```{code-block}
:class: technote-wide-content

GET /ook/links/domains/sdm/schemas/:schema/tables/:table/columns/:column
```

This endpoint requires that links are contextually associated with a specific SDM schema, table, and column.
To provide links with this context, the database schema includes additional tables for each annotating the domain entity associated with the links.
For example, the SDM entity links are stored in tables `links_sdm_schemas`, `links_sdm_tables`, and `links_sdm_columns`.
These tables are related to the parent `links` table through joined-table inheritance.

The link subtype tables provide entity-specific context.
For SDM links, the link subtypes have relationships to a separate set of tables that describe the SDM schema, tables, and columns.
By joining across the `links` table to the subtypes and through to the SDM schema tables, Ook is able to provide links associated with specific SDM schemas, tables, and columns.

### Modeling domain knowledge in Ook

A by-product of this work is that Ook now has a structured model of the domain entities that it indexes.
Here's Ook's databases contain the Science Data Model Schemas as ingested from the source GitHub repository.
This information can have interesting applications beyond the links API by providing a structured and accessible source of truth for a broad set of domains across Rubin Observatory.
For example, documentation discussing the SDM could have dynamic references to the SDM data in Ook to ensure that their documentation is always up-to-date with the latest schema.
This concept is discussed in [SQR-087 Structured information service: preliminary notes](https://sqr-087.lsst.io/).

(datalinker-service)=
## VO documentation linking

From the Rubin Science Platform, clients won't directly query the Ook link service.
Instead, they will query a VO data linking service that uses the Ook link service as a backend.
As a specific example [datalinker][datalinker] is a Python project that hosts data linking endpoints for the RSP for use the [DataLink][datalink] protocol.

There are two parts to the [DataLink][datalink] specification: service descriptors and the link endpoints.

### Service descriptors for TAP schema documentation

DataLink service descriptors annotate a result with metadata about link endpoints that can be called by the client to get information related to the result.
For a TAP query result, the service descriptor would be embedded in the result's VOTable under a `RESOURCE` element with a `type="meta"` attribute.

```{note}
For a TAP schema query result, is this also the case?
```

For the RSP, datalink service descriptors are built from templates hosted in the [sdm_schemas][sdm_schemas] repository.

```{literalinclude} service-descriptor-example.xml
:class: technote-wide-content
:language: xml
```

```{note}
Questions:

- What is the ID in this case?
- What parameters can we meaningfully pass to the link endpoint? For example, can we specify a way to include all columns in a table? Can be specify a subset of columns?
- Can the same link endpoint both describe a table itself and all its columns? Or is that two different services?
```

### Link endpoints for documentation

The link endpoints, which are outlined by the service descriptors, respond with VOTables of documentation links.

The link endpoints derive their data from the {ref}`Ook links API <ook-links-api>`, and in fact the Ook links API generally mirrors the datalink endpoints for entity documentation links.
The differences are that the datalink endpoint requests are authenticated with RSP credentials and that responses are VOTables.
The VO datalink service should ideally cache responses from the Ook link service since the responses are generally stable and apply to all RSP users.


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
