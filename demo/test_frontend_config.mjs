// Actual TypeScript API client, transpiled in memory. No server/storage/network.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { SourceTextModule, SyntheticModule, createContext } from 'node:vm';
import { test } from 'node:test';

const require = createRequire(import.meta.url);
const ts = require('../frontend/node_modules/typescript/lib/typescript.js');
const source = readFileSync(fileURLToPath(new URL('../frontend/src/api/client.ts', import.meta.url)), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;

async function loadClient(environment) {
    let configuration;
    const calls = [];
    const client = {
        interceptors: { request: { use() {} }, response: { use() {} } },
        post(...args) { calls.push(args); return Promise.resolve({ data: {} }); },
    };
    const context = createContext({ URL, URLSearchParams, console,
        localStorage: { getItem() { throw new Error('Browser storage forbidden'); }, setItem() { throw new Error('Browser storage forbidden'); } },
        fetch() { throw new Error('Network forbidden'); },
    });
    const axios = new SyntheticModule(['default'], function () {
        this.setExport('default', { create(config) { configuration = config; return client; } });
    }, { context });
    const module = new SourceTextModule(compiled, { context,
        initializeImportMeta(meta) { meta.env = environment; },
    });
    await module.link(name => { assert.equal(name, 'axios'); return axios; });
    await module.evaluate();
    return { configuration, calls, exports: module.namespace };
}

test('demo build has no relative/production fallback without explicit API origin', async () => {
    await assert.rejects(loadClient({ VITE_FWMS_DEMO_MODE: 'true' }), /no API fallback/);
});
test('demo rejects credential-bearing, path-bearing and insecure public API origins', async () => {
    for (const value of ['http://public.example.com', 'https://user:synthetic@example.com',
        'https://example.com/api', 'https://example.com?token=synthetic']) {
        await assert.rejects(loadClient({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: value }), /Invalid dedicated demo/);
    }
});
test('dedicated HTTPS demo destination and credential behavior', async () => {
    const { configuration } = await loadClient({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: 'https://demo-backend.example.com' });
    assert.equal(configuration.baseURL, 'https://demo-backend.example.com/api');
    assert.equal(configuration.withCredentials, true);
});
test('dedicated localhost origin accepted and trailing slash normalized', async () => {
    const { configuration } = await loadClient({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: 'http://localhost:8001/' });
    assert.equal(configuration.baseURL, 'http://localhost:8001/api');
});
test('institutional API selection remains unchanged', async () => {
    assert.equal((await loadClient({})).configuration.baseURL, '/api');
    assert.equal((await loadClient({ VITE_API_URL: 'https://institutional.example.com' })).configuration.baseURL,
        'https://institutional.example.com/api');
});
test('existing default demo request has no body; role is a whitelisted query option', async () => {
    const { calls, exports } = await loadClient({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: 'http://localhost:8001' });
    await exports.demoLogin();
    assert.equal(calls[0][0], '/auth/demo-login');
    assert.equal(calls[0][1], undefined);
    assert.equal(calls[0][2], undefined);
    await exports.demoLogin('faculty');
    assert.equal(calls[1][2].params.role, 'faculty');
});
