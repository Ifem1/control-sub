#!/usr/bin/env node
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)), '..');
const entry=resolve(root,'node_modules','genlayer','dist','index.js');
const rpc='https://studio.genlayer.com/api';
const guard=()=>{
  const result=spawnSync(process.execPath,[resolve(root,'scripts/guard_studionet.mjs')],{
    cwd:root,stdio:'inherit',env:process.env});
  if(result.status!==0) process.exit(result.status||1);
};
const run=(args)=>{
  guard(); // Re-verify chain immediately before every signed CLI operation.
  const result=spawnSync(process.execPath,[entry,...args],{cwd:root,stdio:'inherit',env:process.env});
  if(result.status!==0) process.exit(result.status||1);
};
// This script intentionally deploys only the primitive. The consumer needs the
// actual primitive address, charter ID/hash, and action hash from verified chain
// state; deploy it in a second guarded phase after those values are known.
run(['deploy','--contract','contracts/controlsub.py','--rpc',rpc]);
