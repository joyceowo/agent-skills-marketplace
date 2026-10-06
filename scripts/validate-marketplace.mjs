// Repository consistency checks; use host validators for their full schemas.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, realpathSync, statSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(process.argv[2] ?? join(dirname(fileURLToPath(import.meta.url)), '..'));
const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));
const kebabCase = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function containedDirectory(base, path) {
  assert(typeof path === 'string' && path.startsWith('./'), `Expected a ./ path: ${path}`);
  assert(!path.includes('\\') && !path.split('/').includes('..'), `Invalid path: ${path}`);
  const target = realpathSync(resolve(base, path));
  const offset = relative(realpathSync(base), target);
  assert(offset && !offset.startsWith('..') && !isAbsolute(offset), `Path escapes root: ${path}`);
  assert(statSync(target).isDirectory(), `Not a directory: ${path}`);
  return target;
}

function entriesByName(marketplace, host) {
  assert(Array.isArray(marketplace.plugins) && marketplace.plugins.length, `${host}: no plugins`);
  const entries = new Map();
  for (const entry of marketplace.plugins) {
    assert(typeof entry.name === 'string' && kebabCase.test(entry.name), `${host}: invalid plugin name`);
    assert(!entries.has(entry.name), `${host}: duplicate plugin ${entry.name}`);
    entries.set(entry.name, entry);
  }
  return entries;
}

try {
  const codex = readJson(join(root, '.agents/plugins/marketplace.json'));
  const claude = readJson(join(root, '.claude-plugin/marketplace.json'));
  assert(typeof codex.name === 'string' && kebabCase.test(codex.name), 'Invalid marketplace name');
  assert.equal(claude.name, codex.name, 'Marketplace names differ');
  assert(claude.owner?.name?.trim(), 'Claude marketplace needs an owner name');

  const codexEntries = entriesByName(codex, 'Codex');
  const claudeEntries = entriesByName(claude, 'Claude');
  const names = [...codexEntries.keys()].sort();
  assert.deepEqual([...claudeEntries.keys()].sort(), names, 'Host plugin lists differ');
  const directories = readdirSync(join(root, 'plugins'), { withFileTypes: true })
    .filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
  assert.deepEqual(directories, names, 'Each plugin directory must appear in both marketplaces');

  for (const name of names) {
    const codexEntry = codexEntries.get(name);
    const claudeEntry = claudeEntries.get(name);
    assert.equal(codexEntry.source?.source, 'local', `${name}: expected a local source`);
    assert.equal(codexEntry.source.path, `./plugins/${name}`, `${name}: source must match directory`);
    assert.equal(claudeEntry.source, codexEntry.source.path, `${name}: host sources differ`);
    assert(['NOT_AVAILABLE', 'AVAILABLE', 'INSTALLED_BY_DEFAULT'].includes(codexEntry.policy?.installation),
      `${name}: invalid Codex installation policy`);
    assert(['ON_INSTALL', 'ON_USE'].includes(codexEntry.policy?.authentication),
      `${name}: invalid Codex authentication policy`);
    assert(codexEntry.category?.trim(), `${name}: missing Codex category`);

    const pluginRoot = containedDirectory(root, claudeEntry.source);
    const codexPlugin = readJson(join(pluginRoot, '.codex-plugin/plugin.json'));
    const claudePlugin = readJson(join(pluginRoot, '.claude-plugin/plugin.json'));
    assert.equal(codexPlugin.name, name, `${name}: manifest name differs from marketplace entry`);
    for (const field of ['name', 'version', 'description', 'author', 'skills', 'repository', 'homepage', 'keywords']) {
      assert.deepEqual(claudePlugin[field], codexPlugin[field], `${name}: manifests differ at ${field}`);
    }
    assert(typeof codexPlugin.version === 'string' && codexPlugin.version.trim(), `${name}: missing version`);
    assert.equal(codexPlugin.skills, './skills/', `${name}: use the shared skills directory`);
    const skillsRoot = containedDirectory(pluginRoot, codexPlugin.skills);
    const skills = readdirSync(skillsRoot, { withFileTypes: true }).filter((entry) => entry.isDirectory());
    assert(skills.length, `${name}: no skills found`);
    for (const skill of skills) {
      const skillRoot = containedDirectory(pluginRoot, `./skills/${skill.name}`);
      const content = readFileSync(join(skillRoot, 'SKILL.md'), 'utf8');
      assert(content.replaceAll('\r\n', '\n').startsWith('---\n'), `${name}/${skill.name}: missing frontmatter`);
    }
    console.log(`OK ${name}@${codexPlugin.version}: ${skills.length} shared skill(s)`);
  }
  console.log(`Marketplace consistency passed: ${codex.name} (Codex + Claude Code)`);
} catch (error) {
  console.error(`Marketplace consistency failed: ${error.message}`);
  process.exitCode = 1;
}
