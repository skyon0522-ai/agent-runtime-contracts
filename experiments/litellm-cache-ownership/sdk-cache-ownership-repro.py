import json

import litellm
from litellm.types.caching import LiteLLMCacheType


def new_cache() -> litellm.Cache:
    return litellm.Cache(type=LiteLLMCacheType.LOCAL)


first = new_cache()
second = new_cache()
assert first.supported_call_types is not None
assert second.supported_call_types is not None
reference_default = list(first.supported_call_types)
first.supported_call_types.clear()
third = new_cache()
assert third.supported_call_types is not None

print(
    json.dumps(
        {
            "reference_default": reference_default,
            "outputs": {
                "cache_1_after_clear": first.supported_call_types,
                "cache_2_after_first_clear": second.supported_call_types,
                "cache_3_new_default": third.supported_call_types,
            },
        },
        sort_keys=True,
    )
)
