# Deep linking to data documentation with IVOA DataLink

```{abstract}
When presenting LSST data through VO services, we want to annotate that data with links to documentation, such as the table and column descriptions in data release documentation sites hosted on ``lsst.io``.
This technote describes a system where we implement a linking service that uses the IVOA DataLink standard to provide links to table and column documentation.
This link service, which resides in the Rubin Science Platform (RSP), is called by TAP schema queries.
In turn, the link service queries Ook, Rubin Observatory's documentation metadata service that indexes the link inventories of documentation sites.
These link inventories are prepared and included with Sphinx documentation builds using Sphinx extensions provided by the Documenteer package.
With this standards-based approach, clients like the Portal can show descriptions and links to documentation from their user interfaces.
```

## Add content here

See the [Documenteer documentation](https://documenteer.lsst.io/technotes/index.html) for tips on how to write and configure your new technote.
