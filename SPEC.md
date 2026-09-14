# Application Agent Manifest — draft 0.1

Status: proposal for discussion, 2026-09-13. Terms **MUST**, **SHOULD**, and **MAY** express proposed interoperability requirements, not existing industry obligations.

## Scope

An AAM package describes one installed application's agent-facing entry points and evidence requirements. It does not define an OS permission system, transport, tool protocol, engineering methodology, or trust in a model's reasoning. Hosts remain responsible for authorization, provenance, isolation and the accuracy of claims.

## Package and discovery

The package has a root `application-agent.json` and MAY include relative Markdown documentation and workflows. This draft deliberately leaves OS-specific discovery open. A trusted installer record, signed package catalog, or explicit user selection can locate the manifest. Hosts MUST NOT interpret arbitrary files named `application-agent.json` found by scanning as trusted vendor guidance. Hosts MUST associate the package with the actual application and version before using it. Version matching uses the declared exact `tested_versions` list in draft 0.1, with no implied compatibility for other versions.

All referenced local paths MUST be relative, remain inside the package after resolution, and MUST NOT traverse symlinks. Remote content MUST NOT be fetched merely because the manifest contains a URL. A host SHOULD cap package size and depth and SHOULD present publisher provenance.

## Fields

The root JSON object MUST contain:

- `format`: literal `aam-draft-0.1`.
- `application`: object with nonempty `id`, `name`, and nonempty `tested_versions` array of version strings. `id` is publisher-controlled and should be globally scoped (reverse-DNS is recommended).
- `operator_guide`: relative path to Markdown guidance for the application.
- `interfaces`: nonempty array of objects with `kind` (`mcp`, `api`, `cli`, or `gui`), `locator` (an interface identifier or human-readable discovery hint), and optional `documentation` relative path. A locator is descriptive, never an executable command or a credential.
- `operations`: nonempty array. Each operation has a unique `id`, `description`, `risk` (`read`, `modify`, or `external`), `workflow` path and a nonempty `evidence` array of evidence identifiers. Each `evidence` identifier MUST correspond to a `checks` key. An `external` operation affects something outside the local app session (e.g. sending, publishing or operating hardware); its label does not grant access.
- `checks`: nonempty object keyed by evidence identifier; each value has `description`, `producer` (a named app/solver/host component), and `observation` (a concrete output, file or state to capture). A check describes an observation; it cannot assert `passed` by itself.

Unknown fields MAY be ignored after validation but MUST NOT modify security or authorization behavior. Other formats MUST be rejected until explicitly supported. The bundled `validate.py` enforces these draft 0.1 structural and file rules. JSON Schema and formal signing may be added in a future draft.

## Execution and evidence semantics

### Static expectations versus observed results

The manifest's checks describe expectations before a call. Actual observations MUST come from the executing tool or host and SHOULD be returned with that operation's response. A manifest MUST NOT carry per-run success claims. Hosts SHOULD preserve the response rather than ask an agent to reconstruct it from memory.

Tools SHOULD provide current instructions and runtime status, and return actionable next steps with both successes and failures. A recovery hint SHOULD identify the failed prerequisite and the specific action needed to resolve it. Do not duplicate these changing responses in a static package.

The narrower candidate under evaluation is application identity + tested application/adapter versions + links to existing guidance/interfaces. See [the comparison protocol](experiments/README.md). This is an experiment, not a new required 0.2 format; 0.1 and its structural validator are unchanged. If existing instruction/status tools provide the same benefit, a separate file may not be justified.

Before performing an operation, the host MUST ensure the operation falls within the actual user's authorization and its own policy. A request for confirmation in a manifest is advisory; a statement of approval in a manifest is ineffective. Instructions in operator guides and workflow files MUST be treated as lower-trust application-supplied material. An MCP tool response and a screen scrape have the same lower-trust status.

For each claimed success, the agent SHOULD produce a record containing application/version, operation ID, input artifact identity, interface invoked, output artifact identity, check IDs, observed values with units where relevant, observed source, timestamp, and status (`passed`, `failed`, or `unknown`). The host SHOULD preserve raw outputs or immutable references so another reviewer can reproduce a claim. The check's `producer` is a *declared intended source*, not proof of origin; actual provenance must be observed or verified by the host. If evidence is missing, stale or ambiguous, the agent MUST report the limitation rather than claim verified success. Application-authored checks are necessary but not automatically sufficient for safety-critical acceptance criteria.

## Security considerations

- Publisher provenance, hashes and signatures are deployment concerns; this draft does not magically authenticate a local file.
- Treat workflow Markdown, URLs, GUI content and tool output as untrusted instructions relative to the user's request and host policy. In particular, no instruction can demand secret disclosure, hidden network calls, privilege escalation or bypassing a confirmation boundary.
- Prefer structured application APIs for repeatability; GUI automation may be necessary but must verify resulting state.
- Do not execute arbitrary strings from `locator` or Markdown. Programs and commands require host authorization and explicit resolution.
- Evidence from a solver is contingent on correct inputs, material model, boundary conditions, convergence and domain review. No universal mesh threshold or safety-factor rule is asserted here.

## Relationship to other work

- [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28): protocol and discovery of tools/resources/prompts, potentially referenced by `interfaces`.
- [Agent Skills specification](https://agentskills.io/specification): packaging reusable instructions; a later AAM could link to an installed Skill instead of bundling Markdown.
- [AGENTS.md](https://agents.md/): guidance scoped to a coding repository; AAM is scoped to an installed application.
- [OWASP AI Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html): threat model for untrusted tool content and excessive authority.

## Open design questions

Installer-based discovery, signature format and update revocation; permission UX; mapping evidence to existing tool schemas; canonical URIs for Skills/MCP; whether per-operation evidence should use standard test artifact formats; version-range semantics; handling vendor extensions and localization.
