#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

function canonicalize(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`)
    .join(',')}}`
}

function compactManifest(manifest, digest) {
  return {
    protocol: manifest.protocol,
    protocol_version: manifest.protocol_version,
    manifest_version: manifest.manifest_version,
    manifest_digest: digest,
    wire_operation: manifest.wire_operation,
    policy_capabilities: manifest.policy_capabilities,
    action_classes: manifest.action_classes,
    facades: Object.fromEntries(
      manifest.facades.map((facade) => [
        facade.model_name,
        {
          family: facade.family,
          kind: facade.kind,
          policy_capability: facade.policy_capability,
          action_class: facade.action_class,
          ...(facade.cases ? { cases: facade.cases } : {})
        }
      ])
    )
  }
}

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const sourcePath = process.argv[2]
if (!sourcePath) throw new Error('Usage: generate-browser-contract.js <canonical-manifest>')

const manifest = JSON.parse(readFileSync(sourcePath, 'utf8'))
const digest = `sha256:${createHash('sha256').update(canonicalize(manifest)).digest('hex')}`
const contractPath = resolve(
  repositoryRoot,
  'skills/xiaohongshu/contracts/browser-manifest.v2.compact.json'
)
const skillPath = resolve(repositoryRoot, 'skills/xiaohongshu/SKILL.md')
const contract = compactManifest(manifest, digest)
writeFileSync(contractPath, `${JSON.stringify(contract, null, 2)}\n`)

const skill = readFileSync(skillPath, 'utf8')
  .replace(/^(    protocol_version: ).+$/m, `$1${manifest.protocol_version}`)
  .replace(/^(    manifest_version: ).+$/m, `$1${manifest.manifest_version}`)
  .replace(/^(    manifest_digest: ).+$/m, `$1${digest}`)
  .replace(/^(    wire_operation: ).+$/m, `$1${manifest.wire_operation}`)
writeFileSync(skillPath, skill)

console.log(`${digest} (${manifest.facades.length} facades)`)