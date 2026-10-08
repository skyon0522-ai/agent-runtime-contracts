# Archived LiteLLM cache ownership experiment

This optional archive preserves a local LiteLLM cache-list ownership reproduction formerly packaged in Casebook. It is separate from the smolagents corpus and requires its own compatible LiteLLM environment and complete source trees.

## Preserved files

- [Reproduction and recorded scope](public-review.reproduction.en.md)
- [Validation record](public-review.validation.en.json)
- [LOCAL-cache reproduction script](sdk-cache-ownership-repro.py)
- [Locally prepared patch](authored-change.patch)
- [Upstream MIT notice](upstream-LICENSE.txt)

All five files were copied byte for byte. The inspected upstream base is `68c0a972a7ff38255a6f0e40336af0ad443695ae`; the validation record identifies the local patch tip and source hashes. Preserve the upstream notice with copied code or substantial excerpts.

## Use and evidence boundary

Follow the archived reproduction instructions in a separate, already prepared LiteLLM environment. The script creates actual LOCAL `litellm.Cache` objects. Agent Runtime Contracts' dependency files, CLI and test corpus provide the smolagents experiment; this archive adds no LiteLLM dependency or core cases.

The archived validation records **30 tests passing** in the original complete-source environment. That result is historical: migration did not rerun the LiteLLM reproduction or those tests. The patch was prepared locally, and the archived record identifies existing [issue #44915](https://github.com/BerriAI/litellm/issues/44915) and [another contributor's PR #45004](https://github.com/BerriAI/litellm/pull/45004) covering the same repair. The archive does not establish upstream acceptance.
