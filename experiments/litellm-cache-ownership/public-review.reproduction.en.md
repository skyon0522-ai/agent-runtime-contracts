# Local SDK proof of cache-list isolation

This casebook export accompanies the exact two-file diff between upstream base `68c0a972a7ff38255a6f0e40336af0ad443695ae` and local tip `cd76b98c727e922af3d6a35f408220816783c65d`.

The reproduction creates two actual `litellm.Cache` objects using the LOCAL backend, clears the first object's `supported_call_types`, and constructs a third object. Before the fix, all three lists were empty after that clear. After the fix, their lengths were 0, 14, and 14. The second and third objects retained the original defaults. No model provider, cloud resource, credential, or mock was used.

Use the accompanying `sdk-cache-ownership-repro.py` with an already prepared compatible environment and complete source trees. Run the same command once against a separate unmodified tree at the stated base and once against the corresponding patched tree. `VENV`, `SOURCE`, and `REPRO` below are reader-selected paths, not supplied credentials or installation instructions.

```bash
cd "$SOURCE"
PYTHONPATH=. "$VENV/bin/python" "$REPRO"
```

The recorded scoped check was:

```bash
PYTHONPATH=. "$VENV/bin/pytest" tests/unit/caching/test_caching.py -q
```

It returned 30 passed with one Pydantic `ReadOnly` warning in 41.20 seconds. The added regressions cover default-instance isolation, caller-owned input lists, caller mutation after construction, empty lists, and `None`.

These executions occurred on the complete exact-base source before the local commit was created. Subsequent inspection confirmed that the committed source and test blobs equal those tested files byte for byte. The sparse Git checkout cannot run the SDK on its own because required package modules are absent. Packaging did not rerun tests or alter a working tree.

The authored change is the per-instance list copy and its two associated regression tests. The dependency remains work by BerriAI and its contributors. The patch touches two non-enterprise paths covered by the inspected MIT terms. Keep the accompanying upstream license notice with copied code or substantial excerpts.

Validation covers the scoped tests and changed-file lint and format checks. Repository-wide lint and remote CI were not run, and this patch was not submitted upstream. Existing issue #44915 and another contributor's PR #45004 cover the same repair. This material records the local behavior change and does not claim production delivery or upstream acceptance.
