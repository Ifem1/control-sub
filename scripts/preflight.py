#!/usr/bin/env python3
"""Offline static project checks; intentionally does not claim live runtime proof."""
from pathlib import Path
import ast, json, sys
root=Path(__file__).resolve().parents[1]
contract=root/'contracts/controlsub.py'
consumer=root/'contracts/controlsub_consumer.py'
for f in (contract,consumer):
    code=f.read_text('utf-8')
    assert code.startswith('# { "Depends": "py-genlayer:'),f
    ast.parse(code,filename=str(f))
source=contract.read_text('utf-8')
assert 'gl.vm.run_nondet_unsafe' in source
assert 'gl.nondet.web.get(' in source
assert 'gl.nondet.exec_prompt(' in source
assert '_read_sources(controls)' in source
assert '_normalize_assessment(own,' in source
assert 'if not isinstance(leader_result, gl.vm.Return)' in source
assert 'SUBMITTED' in source and 'RATIFIED' in source and 'REVOKED' in source
assert '61997' not in (root/'package.json').read_text('utf-8')
pkg=json.loads((root/'package.json').read_text('utf-8'))
assert pkg['devDependencies']['genlayer']=='0.39.1'
for name in ('README.md','docs/CONSENSUS.md','docs/THREAT_MODEL.md','docs/INTEGRATION.md'):
    assert (root/name).is_file(),name
print('STATIC PREFLIGHT OK: code, consensus, storage, network pin, documentation')
