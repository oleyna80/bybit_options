# Optional Repository Graph Provider

This is documentation for an unadmitted optional external capability, not an
installed or admitted integration adapter. No provider is selected, configured,
started, indexed, queried, or invoked by this framework.

Before a separately Owner-approved project Work Block uses a provider, the
operator must choose a provider and record the canonical repository root and
revision, selected provider/version, local state location, and creation/refresh
status. Refresh or rebuild local state after material changes or integration.

Provider state is local, derived, rebuildable, non-authoritative, and not
published by default. It cannot grant authority, a write-set, approval,
assurance verdict, canonical/durable-memory effect, or be the sole basis for a
change. Confirm important findings directly against canonical repository source.

Before indexing, the operator must verify that the chosen provider state is
excluded locally. Use `.git/info/exclude` or a global Git exclusion for that
specific location. Do not add a generic graph directory or a committed ignore
rule. Installation/configuration, MCP/API access, hooks, runtime configuration,
embeddings/uploads, credentials, and provider invocation are future,
Owner-approved project work.
