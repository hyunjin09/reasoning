"""Grammar-order infrastructure correction; identical compact-helper semantics."""
from copy import deepcopy
from scripts.stage14d1.contracts_v2 import *

SCHEMAS = deepcopy(SCHEMAS)
query = SCHEMAS['query']['anyOf'][0]
order = ('status', 'subgoal', 'entity', 'entity_id', 'predicate',
         'spatial_reference', 'query', 'answer_value', 'numeric_provenance')
query['properties'] = {key: query['properties'][key] for key in order}
query['required'] = list(order)
