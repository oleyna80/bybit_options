# Repository Graph Provider Opt-In Record

Use this record only after a separately Owner-approved Work Block admits a
specific optional provider. This template does not select, install, configure,
or invoke a provider.

- **Canonical repository root:** [repository-relative or approved canonical root]
- **Canonical revision:** [commit/revision]
- **Selected provider / version:** [provider and observed version]
- **Provider-local state location:** [local path]
- **Creation / refresh status:** [not created | created | refreshed | rebuild required]
- **Local exclusion verified before indexing:** [`.git/info/exclude` | global exclusion | pending]
- **Material-change refresh rule:** rebuild or refresh after material changes or integration

Provider output/state is local, derived, rebuildable, non-authoritative, and
not published by default. It grants no authority, write-set, approval,
assurance verdict, canonical/durable-memory effect, and cannot be the sole basis
for a change. Confirm important findings directly against canonical repository
source.

Do not record credentials, API keys, embeddings, uploads, or provider-local
content here. Provider installation/configuration, indexing/querying, MCP/API,
hooks, runtime configuration, and invocation require their own Owner-approved
scope.
