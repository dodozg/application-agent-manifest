# Application Agent Manifest (AAM) — discussion draft 0.1

**An installed application should be able to tell an AI agent how to discover its interfaces, use them responsibly, and demonstrate what actually happened.**

This is an independent proposal for discussion, **not an adopted standard** or an implementation endorsed by any software vendor. It complements rather than replaces [MCP](https://modelcontextprotocol.io/specification/2026-07-28), [Agent Skills](https://agentskills.io/specification), and [AGENTS.md](https://agents.md/).

MCP exposes callable tools; Agent Skills package reusable procedures; AGENTS.md supplies project instructions. AAM proposes an *application-supplied, version-matched discovery record* linking to those interfaces and procedures, plus machine-readable requirements for what evidence an agent must obtain before making an outcome claim.

## The minimum useful loop

1. The host discovers a manifest through a trusted installation record or a user-selected path. No OS-wide discovery path is standardized by this draft.
2. The host verifies source, application identity, installed version and path boundaries. The host decides what operations the agent is allowed to perform; manifest text never grants permissions.
3. The agent loads only the relevant operator guidance and workflow, chooses an installed interface, and performs the user's task.
4. The host records observed inputs, tool outputs, artifact identities and verification results. Missing checks remain `unknown` or `failed`, never silently become `passed`.
5. The agent reports the result with scope and evidence. For high-stakes engineering, verification prerequisites do not certify design safety; a qualified review may still be necessary.

See [SPEC.md](SPEC.md) for normative proposal text and the [fictional ExampleCAD package](examples/examplecad/.agent/) for a complete instance. No real CAD vendor or installed program is implied by the example.

```bash
python3 validate.py examples/examplecad/.agent/application-agent.json
python3 -m unittest discover -s tests -v
```

The validator uses only the Python standard library. It checks the draft's structural and local-path rules; it does **not** verify a publisher signature, installed software, physical simulations, or truth of an evidence claim.

## Feedback wanted

How should installer-verified discovery work on Windows, Linux and macOS? Should existing Agent Skills be referenced rather than duplicated? What would constitute interoperable evidence for a real application? How can an app publish useful guidance without turning third-party text into agent authority?

## License

The specification, documentation, examples and code are available under the [MIT License](LICENSE).

Initiated by [dodozg](https://github.com/dodozg). Current status: public discussion draft 0.1.

Feedback and proposed changes are welcome through [issues](https://github.com/dodozg/application-agent-manifest/issues) and pull requests.
