#!/usr/bin/env node
/** Deployment boundary: only StudioNet chain 61999 and its exact RPC endpoint. */
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const RPC = 'https://studio.genlayer.com/api';
const CHAIN_ID = 61999;
const pkg = JSON.parse(readFileSync(resolve(root, 'package.json'), 'utf8'));
if (pkg.devDependencies?.genlayer !== '0.39.1') throw new Error('Refusing unpinned GenLayer CLI');
// Invoke the package entry point with the current Node executable. Windows
// cannot reliably spawn a .cmd shim without a shell, and shell execution is
// unnecessary for this fixed, repository-local CLI path.
const entry = resolve(root, 'node_modules', 'genlayer', 'dist', 'index.js');
const installed = spawnSync(process.execPath, [entry, '--version'], {encoding: 'utf8', cwd:root});
const versionText = (installed.stdout||'') + ' ' + (installed.stderr||'');
if (installed.status !== 0 || !versionText.includes('0.39.1'))
  throw new Error('Repository-local genlayer@0.39.1 missing/mismatched: ' + versionText);
const request = async(method) => {
  const response = await fetch(RPC, {
    method:'POST', headers:{'content-type':'application/json'},
    body:JSON.stringify({jsonrpc:'2.0',id:1,method,params:[]}),
    signal:AbortSignal.timeout(20000)
  });
  if (!response.ok) throw new Error(`StudioNet RPC HTTP ${response.status}`);
  const data=await response.json();
  if(data.error) throw new Error(`RPC ${method}: ${JSON.stringify(data.error)}`);
  return data.result;
};
let id;
try {id=await request('eth_chainId');} catch (error) {
  throw new Error(`Could not positively verify StudioNet chain ID from ${RPC}: ${error.message}`);
}
const numeric=typeof id==='string' && id.startsWith('0x') ? Number.parseInt(id,16) : Number(id);
if (numeric!==CHAIN_ID) throw new Error(`Refusing deployment: RPC chain ${numeric} != ${CHAIN_ID}`);
if (process.env.GENLAYER_RPC_URL && process.env.GENLAYER_RPC_URL!==RPC)
  throw new Error('Refusing alternate GenLayer RPC endpoint override');
console.log('STUDIONET VERIFIED: chain 61999, exact RPC, repo-local CLI 0.39.1');
