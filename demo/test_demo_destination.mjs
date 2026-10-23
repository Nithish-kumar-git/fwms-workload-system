// Pure configuration test: no network, browser storage, or backend is used.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createContext, SourceTextModule } from 'node:vm';
import { test } from 'node:test';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const ts = require('../frontend/node_modules/typescript/lib/typescript.js');
const source = readFileSync(fileURLToPath(new URL('../frontend/src/demo/destination.ts', import.meta.url)), 'utf8');
const loginPageSource = readFileSync(fileURLToPath(new URL('../frontend/src/pages/LoginPage.tsx', import.meta.url)), 'utf8');
const compiled = ts.transpileModule(source, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;

async function loadResolver() {
    const context = createContext({ URL });
    const module = new SourceTextModule(compiled, { context });
    await module.link(() => { throw new Error('The destination resolver has no imports'); });
    await module.evaluate();
    return module.namespace.resolveDedicatedDemoDestination;
}

test('an institutional build without a dedicated demo URL cannot fall back to its API', async () => {
    const resolveDestination = await loadResolver();
    assert.equal(resolveDestination(undefined), null);
    assert.equal(resolveDestination(''), null);
});

test('only a credential-free HTTPS dedicated demo URL is accepted', async () => {
    const resolveDestination = await loadResolver();
    assert.equal(resolveDestination('https://demo.example.com/login'), 'https://demo.example.com/login');
    assert.equal(resolveDestination('http://demo.example.com'), null);
    assert.equal(resolveDestination('https://user:password@demo.example.com'), null);
    assert.equal(resolveDestination('not a URL'), null);
});

test('the institutional login handler guards the dedicated destination before calling demoLogin', () => {
    assert.match(loginPageSource, /if \(!isSyntheticDemo\) \{\s*if \(!dedicatedDemoDestination\) \{\s*setError\('Demo is not configured for this site\. Contact the operator\.'\);\s*return;/);
    assert.match(loginPageSource, /window\.location\.assign\(dedicatedDemoDestination\);\s*return;\s*}\s*const res = await demoLogin\(demoRole\);/);
});
