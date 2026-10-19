#!/usr/bin/env node
/** Capture real StudioNet rejection evidence for ControlSub consumer guards. */
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { createAccount, createClient } from 'genlayer-js';
import { CalldataAddress, TransactionStatus } from 'genlayer-js/types';
import { studionet } from 'genlayer-js/chains';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (path) => readFileSync(resolve(root, path), 'utf8');
const fail = (message) => { throw new Error(message); };
const CONTROL_SUB = '0x9ce8C38E919F7BAD4E568aaC105eE05ed51Ac302';
const OWNER = '0xD6423aE82a975d55C6CeaC222827A727325e0459';
const PASSING_CANDIDATE = 2;
const PASSING_CHARTER = 1;
const PASSING_CERTIFICATE = '43ff9e900eb6815c246e0ecba84040c3e860c3555608ab816265a18936663679';
const PASSING_ACTION = createHash('sha256').update('ControlSub neutral demo action v1', 'utf8').digest('hex');
const resultNames = ['IDLE', 'AGREE', 'DISAGREE', 'TIMEOUT', 'DETERMINISTIC_VIOLATION',
  'NO_MAJORITY', 'MAJORITY_AGREE', 'MAJORITY_DISAGREE'];

function guard() {
  const result = spawnSync(process.execPath, [resolve(root, 'scripts/guard_studionet.mjs')], {
    cwd: root, stdio: 'inherit', env: process.env,
  });
  if (result.status !== 0) process.exit(result.status || 1);
}

const privateKey = process.env.CONTROLSUB_TEST_PRIVATE_KEY;
if (!privateKey || !/^0x[0-9a-fA-F]{64}$/.test(privateKey)) {
  fail('Set CONTROLSUB_TEST_PRIVATE_KEY in the process environment; the key is never written to disk.');
}
guard();
const account = createAccount(privateKey);
const client = createClient({ chain: studionet, account });
const emit = (value) => console.log(JSON.stringify(value));
const asInt = (value) => Number(value);

async function finalize(hash, label) {
  const tx = await client.waitForTransactionReceipt({
    hash, status: TransactionStatus.FINALIZED, retries: 120, interval: 5000,
  });
  const leader = tx.consensus_data?.leader_receipt?.[0] ?? tx.leader_receipt?.[0] ?? {};
  const evidence = {
    stage: label,
    hash,
    finality: tx.status_name ?? tx.statusName ?? tx.status,
    consensus: tx.result_name ?? tx.resultName ?? resultNames[tx.result] ?? tx.result,
    execution: leader.execution_result ?? tx.execution_result ?? tx.txExecutionResultName ?? null,
    executionError: leader.genvm_result?.error_description ?? null,
    executionMessage: leader.result?.payload ?? leader.genvm_result?.stderr ?? null,
    returnPayload: leader.result?.payload?.readable ?? leader.result?.payload ?? null,
  };
  emit(evidence);
  if (evidence.finality !== 'FINALIZED' && asInt(evidence.finality) !== 7) {
    fail(`${label} did not finalize; inspect the preserved transaction hash.`);
  }
  return { tx, evidence };
}

async function deployConsumer(charterId, charterHash, actionHash, label) {
  guard();
  const hash = await client.deployContract({
    account, code: read('contracts/controlsub_consumer.py'),
    args: [new CalldataAddress(Buffer.from(CONTROL_SUB.slice(2), 'hex')),
      charterId, charterHash, actionHash],
  });
  const { tx } = await finalize(hash, `${label}_deploy`);
  const address = tx.data?.contract_address ?? tx.txDataDecoded?.contractAddress;
  if (typeof address !== 'string' || !/^0x[0-9a-fA-F]{40}$/.test(address)) {
    fail(`${label} finalized without a readable contract address.`);
  }
  emit({ stage: `${label}_address`, address });
  return address;
}

async function write(address, functionName, args, label) {
  guard();
  const hash = await client.writeContract({ account, address, functionName, args, value: 0n });
  return finalize(hash, label);
}

async function execution(address) {
  return client.readContract({ address, functionName: 'get_execution', args: [] });
}

async function assertRejectedWithoutMutation(address, candidateId, certificateHash, actionHash, label,
  existingTransactionHash = null) {
  const before = await execution(address);
  if (before.executed !== false) fail(`${label} consumer was already executed before the negative call.`);
  const { evidence } = existingTransactionHash
    ? await finalize(existingTransactionHash, label)
    : await write(address, 'execute', [candidateId, certificateHash, actionHash], label);
  const after = await execution(address);
  const rejected = ['ERROR', 'FAILURE', 'FINISHED_WITH_ERROR'].includes(evidence.execution);
  const agreedExecutionResult = evidence.consensus === 'MAJORITY_AGREE';
  emit({ stage: `${label}_readback`, before, after, transactionExecutionRejected: rejected,
    validatorConsensusAgreed: agreedExecutionResult,
    stateUnchanged: JSON.stringify(before) === JSON.stringify(after) });
  if (!rejected || !agreedExecutionResult || after.executed !== false ||
      JSON.stringify(before) !== JSON.stringify(after)) {
    fail(`${label} did not produce a verified execution rejection with unchanged state.`);
  }
}

if (account.address.toLowerCase() !== OWNER.toLowerCase()) {
  fail('Selected key is not the owner of the deployed demonstration charter.');
}
const balanceStart = await client.getBalance({ address: account.address });
const activeCharter = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_charter', args: [PASSING_CHARTER],
});
const activeCandidate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_candidate', args: [PASSING_CANDIDATE],
});
const activeCertificate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_certificate', args: [PASSING_CANDIDATE],
});
const currentlyActive = await client.readContract({
  address: CONTROL_SUB, functionName: 'is_active',
  args: [PASSING_CHARTER, PASSING_CANDIDATE, PASSING_CERTIFICATE, activeCharter.charter_hash],
});
if (activeCharter.owner.toLowerCase() !== OWNER.toLowerCase() ||
    activeCandidate.status !== 5 || activeCandidate.certificate_hash !== PASSING_CERTIFICATE ||
    activeCertificate.is_current !== true || currentlyActive !== true) {
  fail('Existing successful charter/candidate/certificate is not in its expected active state.');
}
emit({ stage: 'positive_state_before_negative_audit', chainId: studionet.id,
  primitive: CONTROL_SUB, charterId: PASSING_CHARTER, candidateId: PASSING_CANDIDATE,
  charterHash: activeCharter.charter_hash, certificateHash: PASSING_CERTIFICATE,
  isActive: currentlyActive, existingConsumer: '0xdfEB10D80179FD2D9cFc8d7590Bcb29657bBE300' });

// A. Correct charter/candidate/action pins, but an invalid certificate.
const priorInvalidConsumer = process.env.CONTROLSUB_NEGATIVE_A_CONSUMER;
const priorInvalidTx = process.env.CONTROLSUB_NEGATIVE_A_TX;
if (Boolean(priorInvalidConsumer) !== Boolean(priorInvalidTx)) {
  fail('Resume certificate-mismatch evidence with both its consumer address and transaction hash.');
}
const invalidCertConsumer = priorInvalidConsumer || await deployConsumer(
  PASSING_CHARTER, activeCharter.charter_hash, PASSING_ACTION, 'negative_invalid_certificate');
if (priorInvalidConsumer) {
  const schema = await client.getContractSchema(priorInvalidConsumer);
  if (!Object.hasOwn(schema.methods ?? {}, 'execute') || !Object.hasOwn(schema.methods ?? {}, 'get_execution')) {
    fail('Prior certificate-mismatch consumer does not have the expected schema.');
  }
  emit({ stage: 'negative_invalid_certificate_reusing_prior_consumer', address: priorInvalidConsumer,
    priorTransaction: priorInvalidTx });
}
await assertRejectedWithoutMutation(invalidCertConsumer, PASSING_CANDIDATE,
  `0x${'0'.repeat(64)}`, PASSING_ACTION, 'negative_invalid_certificate', priorInvalidTx);

// B. Valid certificate, but the ID names the known unratified candidate 1.
const wrongCandidate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_candidate', args: [1],
});
if (wrongCandidate.charter_id !== PASSING_CHARTER || wrongCandidate.status === 5) {
  fail('Candidate 1 is not the expected unratified candidate on charter 1.');
}
emit({ stage: 'negative_wrong_candidate_prestate', candidateId: 1,
  charterId: wrongCandidate.charter_id, status: wrongCandidate.status,
  certificateHash: wrongCandidate.certificate_hash });
const priorWrongCandidateConsumer = process.env.CONTROLSUB_NEGATIVE_B_CONSUMER;
const priorWrongCandidateTx = process.env.CONTROLSUB_NEGATIVE_B_TX;
if (Boolean(priorWrongCandidateConsumer) !== Boolean(priorWrongCandidateTx)) {
  fail('Resume wrong-candidate evidence with both its consumer address and transaction hash.');
}
const wrongCandidateConsumer = priorWrongCandidateConsumer || await deployConsumer(
  PASSING_CHARTER, activeCharter.charter_hash, PASSING_ACTION, 'negative_wrong_candidate');
if (priorWrongCandidateConsumer) {
  const schema = await client.getContractSchema(priorWrongCandidateConsumer);
  if (!Object.hasOwn(schema.methods ?? {}, 'execute') || !Object.hasOwn(schema.methods ?? {}, 'get_execution')) {
    fail('Prior wrong-candidate consumer does not have the expected schema.');
  }
  emit({ stage: 'negative_wrong_candidate_reusing_prior_consumer', address: priorWrongCandidateConsumer,
    priorTransaction: priorWrongCandidateTx });
}
await assertRejectedWithoutMutation(wrongCandidateConsumer, 1,
  PASSING_CERTIFICATE, PASSING_ACTION, 'negative_wrong_candidate', priorWrongCandidateTx);

// C. Create an isolated charter/candidate, ratify and verify it, then revoke it
// with the real charter owner and prove a newly deployed consumer is blocked.
const charterData = JSON.parse(read('examples/charter.json'));
const dimensionJson = JSON.stringify(charterData.dimensions);
const repositoriesJson = JSON.stringify(charterData.allowed_repositories);
const resumedCharterId = Number(process.env.CONTROLSUB_NEGATIVE_CHARTER_ID ?? 0);
let charterId = resumedCharterId;
if (!charterId) {
  const { tx: createCharterTx } = await write(CONTROL_SUB, 'create_charter', [
    'Isolated revocation negative-path audit',
    'Temporary StudioNet demonstration charter for certificate invalidation evidence.',
    charterData.baseline,
    dimensionJson,
    repositoriesJson,
    charterData.certificate_lifetime_days,
  ], 'negative_isolated_create_charter');
  const charterReturn = createCharterTx.consensus_data?.leader_receipt?.[0]?.result?.payload?.readable ??
    createCharterTx.consensus_data?.leader_receipt?.[0]?.result?.payload;
  charterId = Number(charterReturn);
  if (!Number.isSafeInteger(charterId) || charterId <= 1) {
    fail(`Could not decode isolated charter ID from final receipt payload: ${charterReturn}`);
  }
}
const isolatedCharter = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_charter', args: [charterId],
});
if (isolatedCharter.owner.toLowerCase() !== OWNER.toLowerCase()) {
  fail('Isolated charter owner readback does not match the signing test wallet.');
}
emit({ stage: 'negative_isolated_charter_readback', charterId,
  charterHash: isolatedCharter.charter_hash, owner: isolatedCharter.owner });

const controls = JSON.stringify(JSON.parse(read('examples/controls.template.json')));
const resumedCandidateId = Number(process.env.CONTROLSUB_NEGATIVE_CANDIDATE_ID ?? 0);
let candidateId = resumedCandidateId;
if (!candidateId) {
  const { tx: proposeTx } = await write(CONTROL_SUB, 'propose', [
    charterId, 'Pinned reference controls for revocation proof', controls, isolatedCharter.charter_hash,
  ], 'negative_isolated_propose');
  const candidateReturn = proposeTx.consensus_data?.leader_receipt?.[0]?.result?.payload?.readable ??
    proposeTx.consensus_data?.leader_receipt?.[0]?.result?.payload;
  candidateId = Number(candidateReturn);
  if (!Number.isSafeInteger(candidateId) || candidateId <= 2) {
    fail(`Could not decode isolated candidate ID from final receipt payload: ${candidateReturn}`);
  }
}
let isolatedCandidate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_candidate', args: [candidateId],
});
let assessEvidence = null;
const assessmentAttempts = resumedCandidateId ? 1 : 2;
for (let attempt = 1; isolatedCandidate.status === 1 && attempt <= assessmentAttempts; attempt += 1) {
  ({ evidence: assessEvidence } = await write(CONTROL_SUB, 'assess', [
    candidateId, isolatedCandidate.candidate_hash,
  ], `negative_isolated_assess_attempt_${attempt}`));
  isolatedCandidate = await client.readContract({
    address: CONTROL_SUB, functionName: 'get_candidate', args: [candidateId],
  });
  emit({ stage: 'negative_isolated_assessment_attempt_readback', attempt,
    transactionConsensus: assessEvidence.consensus, status: isolatedCandidate.status,
    assessmentHash: isolatedCandidate.assessment_hash });
}
isolatedCandidate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_candidate', args: [candidateId],
});
emit({ stage: 'negative_isolated_assessment_readback', transactionConsensus: assessEvidence?.consensus ?? null,
  status: isolatedCandidate.status, assessment: isolatedCandidate.assessment,
  assessmentHash: isolatedCandidate.assessment_hash });
if (isolatedCandidate.status !== 2) {
  fail('Isolated candidate did not reach ASSESS_PASS; no ratification or revocation was attempted.');
}

await write(CONTROL_SUB, 'ratify', [candidateId, isolatedCandidate.assessment_hash, ''],
  'negative_isolated_ratify');
isolatedCandidate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_candidate', args: [candidateId],
});
let isolatedCertificate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_certificate', args: [candidateId],
});
let isolatedActive = await client.readContract({
  address: CONTROL_SUB, functionName: 'is_active',
  args: [charterId, candidateId, isolatedCandidate.certificate_hash, isolatedCharter.charter_hash],
});
if (isolatedCandidate.status !== 5 || isolatedCertificate.is_current !== true || isolatedActive !== true) {
  fail('Isolated certificate was not verified active before revocation.');
}
emit({ stage: 'negative_isolated_valid_before_revoke', charterId, candidateId,
  certificateHash: isolatedCandidate.certificate_hash, isCurrent: isolatedCertificate.is_current,
  isActive: isolatedActive });

const isolatedAction = createHash('sha256').update('ControlSub isolated revocation action v1', 'utf8').digest('hex');
const revokedConsumer = await deployConsumer(charterId, isolatedCharter.charter_hash,
  isolatedAction, 'negative_revoked_certificate');
await write(CONTROL_SUB, 'revoke', [candidateId, isolatedCandidate.certificate_hash],
  'negative_isolated_revoke');
isolatedCandidate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_candidate', args: [candidateId],
});
isolatedCertificate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_certificate', args: [candidateId],
});
isolatedActive = await client.readContract({
  address: CONTROL_SUB, functionName: 'is_active',
  args: [charterId, candidateId, isolatedCertificate.certificate_hash, isolatedCharter.charter_hash],
});
emit({ stage: 'negative_isolated_revocation_readback', charterId, candidateId,
  candidateStatus: isolatedCandidate.status, certificateStatus: isolatedCertificate.status,
  certificateActive: isolatedCertificate.active, certificateCurrent: isolatedCertificate.is_current,
  isActive: isolatedActive, certificateHash: isolatedCertificate.certificate_hash });
if (isolatedCandidate.status !== 6 || isolatedCertificate.active !== false ||
    isolatedCertificate.is_current !== false || isolatedActive !== false) {
  fail('On-chain revocation state or is_active predicate did not become false.');
}
await assertRejectedWithoutMutation(revokedConsumer, candidateId,
  isolatedCertificate.certificate_hash, isolatedAction, 'negative_revoked_certificate');

const preservedCertificate = await client.readContract({
  address: CONTROL_SUB, functionName: 'get_certificate', args: [PASSING_CANDIDATE],
});
const preservedActive = await client.readContract({
  address: CONTROL_SUB, functionName: 'is_active',
  args: [PASSING_CHARTER, PASSING_CANDIDATE, PASSING_CERTIFICATE, activeCharter.charter_hash],
});
const originalExecution = await client.readContract({
  address: '0xdfEB10D80179FD2D9cFc8d7590Bcb29657bBE300',
  functionName: 'get_execution', args: [],
});
const balanceEnd = await client.getBalance({ address: account.address });
emit({ stage: 'negative_audit_complete', chainId: studionet.id,
  isolatedCharterId: charterId, isolatedCandidateId: candidateId,
  isolatedCertificateHash: isolatedCertificate.certificate_hash,
  passingCertificateStillCurrent: preservedCertificate.is_current,
  passingCertificateStillActive: preservedActive,
  originalPositiveExecution: originalExecution,
  startBalanceWei: balanceStart.toString(), endBalanceWei: balanceEnd.toString() });
