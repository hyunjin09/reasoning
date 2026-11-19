"""Enforce existing LOCATE mode/cardinality at the generation boundary."""
from copy import deepcopy
from scripts.stage14d1_pilot.interface_v5 import (
    QUERY_SCHEMA, build_catalog, compile_query, query_prompt, validate_query,
    validate_address, normalize_address, helper_prompt, SCHEMAS as V5_SCHEMAS,
)
SCHEMAS=deepcopy(V5_SCHEMAS)
branches=[]
for mode,n in [('LOCAL',1),('MULTI',2),('GLOBAL',0),('UNRESOLVABLE',0)]:
    branch=deepcopy(V5_SCHEMAS['locate'])
    branch['properties']['mode']={'const':mode}
    branch['properties']['boxes'].update(minItems=n,maxItems=n)
    branches.append(branch)
SCHEMAS['locate']={'anyOf':branches}
