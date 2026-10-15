#!/usr/bin/env node
/** Execute the complete ControlSub demo lifecycle against guarded StudioNet. */
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

function guard() {
  const result = spawnSync(process.execPath, [resolve(root, 'scripts/guard_studionet.mjs')], {
    cwd: root,
    stdio: 'inherit',
    env: process.env,
  });
  if (result.status !== 0) process.exit(result.status || 1);
}
guard();

const privateKey = process.env.CONTROLSUB_TEST_PRIVATE_KEY;
if (!privateKey || !/^0x[0-9a-fA-F]{64}$/.test(privateKey)) {
  fail('Set CONTROLSUB_TEST_PRIVATE_KEY in the process environment; the key is never written to disk.');
}

const account = createAccount(privateKey);
const client = createClient({ chain: studionet, account });
await client.initializeConsensusSmartContract();
const startBalance = await client.getBalance({ address: account.address });
console.log(JSON.stringify({ stage: 'ready', network: studionet.name, chainId: studionet.id,
  deployer: account.address, balanceWei: startBalance.toString() }));

async function waitFinal(hash, label, allowDisagreement = false) {
  const tx = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.FINALIZED,
    retries: 120,
    interval: 5000,
  });
  const outcome = {
    stage: label,
    hash,
    status: tx.statusName ?? tx.status,
    consensus: tx.result_name ?? tx.resultName ?? tx.result,
  };
  console.log(JSON.stringify(outcome));
  if (tx.statusName !== TransactionStatus.FINALIZED && Number(tx.status) !== 7) {
    fail(`${label} did not finalize successfully; stopping before the next write.`);
  }
  if ((tx.result_name ?? tx.resultName) !== 'MAJORITY_AGREE' && !allowDisagreement) {
    fail(`${label} did not reach validator agreement; stopping before the next write.`);
  }
  return tx;
}

async function write(address, functionName, args, label, allowDisagreement = false) {
  guard();
  const hash = await client.writeContract({ account, address, functionName, args, value: 0n });
  await waitFinal(hash, label, allowDisagreement);
}

async function deploy(path, args, label) {
  guard();
  const hash = await client.deployContract({ account, code: read(path), args });
  const tx = await waitFinal(hash, label);
  const address = tx.data?.contract_address ?? tx.txDataDecoded?.contractAddress;
  if (typeof address !== 'string' || !/^0x[0-9a-fA-F]{40}$/.test(address)) {
    fail(`${label} finalized but the receipt did not contain a contract address.`);
  }
  console.log(JSON.stringify({ stage: `${label}_address`, address }));
  return address;
}

let primitiveAddress = process.env.CONTROLSUB_EXISTING_ADDRESS;
if (primitiveAddress) {
  if (!/^0x[0-9a-fA-F]{40}$/.test(primitiveAddress)) fail('Invalid existing ControlSub address.');
  const schema = await client.getContractSchema(primitiveAddress);
  const methods = Object.keys(schema.methods ?? {});
  for (const method of ['create_charter', 'propose', 'assess', 'ratify', 'get_charter', 'get_candidate']) {
    if (!methods.includes(method)) fail(`Existing contract schema is missing ${method}.`);
  }
  console.log(JSON.stringify({ stage: 'reuse_verified_controlsub', address: primitiveAddress }));
} else {
  primitiveAddress = await deploy('contracts/controlsub.py', [], 'deploy_controlsub');
}

const charterData = JSON.parse(read('examples/charter.json'));
const dimensionsJson = JSON.stringify(charterData.dimensions);
const repositoriesJson = JSON.stringify(charterData.allowed_repositories);
let charterId = Number(process.env.CONTROLSUB_EXISTING_CHARTER_ID ?? 0);
if (!charterId) {
  await write(primitiveAddress, 'create_charter', [
    charterData.title,
    charterData.context,
    charterData.baseline,
    dimensionsJson,
    repositoriesJson,
    charterData.certificate_lifetime_days,
  ], 'create_charter');
  charterId = 1;
}

const charter = await client.readContract({
  address: primitiveAddress, functionName: 'get_charter', args: [charterId],
});
if (String(charter.owner).toLowerCase() !== account.address.toLowerCase()) {
  fail('On-chain charter owner does not match the selected test wallet.');
}

const controls = JSON.stringify(JSON.parse(read('examples/controls.template.json')));
let candidateId = Number(process.env.CONTROLSUB_EXISTING_CANDIDATE_ID ?? 0);
if (!candidateId) {
  await write(primitiveAddress, 'propose', [charterId, 'Gateway and review controls', controls, charter.charter_hash], 'propose');
  candidateId = 1;
}
let candidate = await client.readContract({
  address: primitiveAddress, functionName: 'get_candidate', args: [candidateId],
});
for (let attempt = 1; Number(candidate.status) === 1 && attempt <= 2; attempt += 1) {
  await write(primitiveAddress, 'assess', [candidateId, candidate.candidate_hash], `assess_attempt_${attempt}`, true);
  candidate = await client.readContract({
    address: primitiveAddress, functionName: 'get_candidate', args: [candidateId],
  });
  if (Number(candidate.status) === 1) {
    console.log(JSON.stringify({ stage: 'assessment_still_pending', attempt }));
  }
}
if (![2, 5].includes(Number(candidate.status)) || !candidate.assessment_hash) {
  console.log(JSON.stringify({ stage: 'assessment_result', status: Number(candidate.status),
    assessment: candidate.assessment ?? null }));
  fail('Consensus assessment did not PASS; stopping without owner ratification or consumer deployment.');
}

if (Number(candidate.status) !== 5) {
  await write(primitiveAddress, 'ratify', [candidateId, candidate.assessment_hash, ''], 'ratify');
  candidate = await client.readContract({
    address: primitiveAddress, functionName: 'get_candidate', args: [candidateId],
  });
}
const certificate = await client.readContract({
  address: primitiveAddress, functionName: 'get_certificate', args: [candidateId],
});
if (certificate.active !== true || certificate.is_current !== true || !certificate.certificate_hash) {
  fail('The on-chain certificate is not current and active; stopping before consumer deployment.');
}

const actionHash = createHash('sha256').update('ControlSub neutral demo action v1', 'utf8').digest('hex');
let consumerAddress = process.env.CONTROLSUB_EXISTING_CONSUMER_ADDRESS;
if (consumerAddress) {
  const schema = await client.getContractSchema(consumerAddress);
  if (!Object.hasOwn(schema.methods ?? {}, 'execute') || !Object.hasOwn(schema.methods ?? {}, 'get_execution')) {
    fail('Existing consumer schema is missing required methods.');
  }
} else {
  consumerAddress = await deploy('contracts/controlsub_consumer.py', [
    new CalldataAddress(Buffer.from(primitiveAddress.slice(2), 'hex')),
    charterId,
    charter.charter_hash,
    actionHash,
  ], 'deploy_consumer');
}

let execution = await client.readContract({
  address: consumerAddress, functionName: 'get_execution', args: [],
});
if (execution.executed !== true) {
  await write(consumerAddress, 'execute', [candidateId, certificate.certificate_hash, actionHash], 'execute_consumer');
  execution = await client.readContract({
    address: consumerAddress, functionName: 'get_execution', args: [],
  });
}
if (execution.executed !== true || Number(execution.candidate_id) !== candidateId ||
    Number(execution.charter_id) !== charterId ||
    String(execution.owner).toLowerCase() !== account.address.toLowerCase() ||
    execution.charter_hash !== charter.charter_hash ||
    execution.certificate_hash !== certificate.certificate_hash || execution.action_hash !== actionHash) {
  fail('The consumer state does not match the expected one-shot certified execution.');
}

const endBalance = await client.getBalance({ address: account.address });
console.log(JSON.stringify({
  stage: 'cycle_complete',
  primitiveAddress,
  consumerAddress,
  charterId,
  charterHash: charter.charter_hash,
  candidateId,
  assessmentHash: candidate.assessment_hash,
  certificateHash: certificate.certificate_hash,
  actionHash,
  execution,
  startBalanceWei: startBalance.toString(),
  endBalanceWei: endBalance.toString(),
}));
