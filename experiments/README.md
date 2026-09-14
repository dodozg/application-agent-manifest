# Test the need for a smaller application discovery record

Status: runnable fixture and comparison protocol. **No fresh-agent trials have been run or measured.** Unit tests exercise the tool, not agent performance. The SQL engine is real SQLite, supplied with Python; the wrapper is project-owned demo software, not a vendor integration. This JSON CLI is not an MCP server.

## Hypothesis and design change

Community feedback suggests most useful guidance belongs in instructions/status tools and actionable operation responses. The potentially distinct part of AAM is matching installed versions to documentation and locating the right interface before interaction.

The experiment tests that narrower claim. Discovery contains identity, actual SQLite and wrapper versions, and references to live instructions/status. It contains no operation outcomes and no copied error handbook. The generated `discovery.json` is explicitly experimental and is **not** valid input for the original 0.1 validator.

## Run the real operation

From the repository root with Python 3.9 or later:

```bash
python3 experiments/sqlite_export.py --setup /tmp/aam-trial-001
echo '{"action":"status"}' | python3 experiments/sqlite_export.py /tmp/aam-trial-001
echo '{"action":"instructions"}' | python3 experiments/sqlite_export.py /tmp/aam-trial-001
```

Use a new trial directory; setup refuses an existing directory. On Windows choose an equivalent writable new path. Send one JSON object to stdin per tool call. For `export`, provide `output`, `expected_application_version` and `expected_adapter_version`, copied from live status. Responses always include runtime information, a code and next steps. Version mismatch and existing output return explicit recovery instructions. Success includes observed row count, quick_check, output size, SHA-256 and read-back verification against the selected SQLite snapshot. No account is required, so status explicitly reports that instead of inventing an account tool.

## Equal baseline and treatment

Use the same model/version/settings, user goal, call budget and tool descriptions in both conditions. Permit the agent to call the wrapper only, plus read `discovery.json` in condition B; a host adapter must enforce this, not merely request it in the prompt. Do not expose implementation source, this protocol, other trials or hidden judge data. No separate-file requirement should be baked into the task.

| Condition | Available information |
| --- | --- |
| A: live tools only | status, instructions, export with full evidence and recovery responses |
| B: same tools + discovery | Exactly A, plus the generated discovery record supplied by the host |

The same version precondition is enforced in A and B. Status exposes runtime versions in both, so the control is not artificially deprived of information. A tie or an advantage for A is a valid result. This fixture does not test installer-level discovery, since both conditions already know how to call the tool.

Use this identical user task:

> Export all products from the available database into a new CSV. Preserve existing files. Report the number of data rows and the SHA-256 of the exported file, based on the tool's observed results.

## Scenarios and fresh sessions

1. Clean fixture: no existing export.
2. Collision: host creates `products.csv` containing `keep me` before the session; successful recovery uses another filename without modifying the existing file.
3. Stale discovery: same scenario as clean, but B's discovery record has adapter version `stale-test-value`; the running wrapper is unchanged. A still has live tools only. This intentionally tests stale metadata recovery, not a simulated real application upgrade. A genuine breaking-version upgrade remains future work.

For each scenario, randomize A/B order in matched pairs; start a new session and fresh directory each run. During pilot work, inspect where agents get stuck, improve live responses for **both** conditions, and retry. Freeze wrapper/prompt/model/settings before measured trials; keep pilot runs separate. Start with 10 measured pairs per scenario (60 sessions total); this is exploratory, not proof of a general standard. Stop each session at 15 tool calls, 5 minutes, or the first request for human intervention. Count timeouts and interventions as failures.

## Host judging and recording

The host must independently check the CSV bytes against `id,name,quantity\n1,Bolt,12\n2,Nut,18\n3,Washer,24\n`, hash the actual file, compare the agent's final row count/hash, and verify the original source and pre-existing files are unchanged. A tool's `ok` field alone is not the judge.

For every trial save transcript plus: trial ID, scenario, condition, model/settings, repository commit, runtime versions, success, tool calls, failed calls, human interventions, elapsed seconds, output path/hash and judge findings. Keep failures, not only successful examples. Report paired success differences and distributions of calls/time, not just a single average. A small trial cannot establish universal reliability or causal benefit across applications.

Promote a separate convention only if B shows a repeatable practical benefit beyond descriptive response improvements. First agree what benefit justifies maintenance costs; one possible exploratory gate is at least 20% fewer calls on successful paired runs with no decrease in success and no file-preservation regressions. This threshold is a decision aid, not a statistical significance test. Replicate on another application and a real version upgrade before standardizing. If A performs equally well, retain the response design guidance and reconsider a separate file.

## What is verified today

```bash
python3 -m unittest discover -s tests -v
```

Tests check real CSV output against independently specified expected bytes, source preservation, stale-version recovery, collision recovery, path containment, symlink overwrite refusal and corrupt-source failure, plus the original draft validator checks. They do not measure an LLM or establish that AAM is useful. Fresh-session agent execution and the host-enforced experimental runner remain unimplemented.
