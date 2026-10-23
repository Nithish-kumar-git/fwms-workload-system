// Deployment configuration checks + real isolated demo build; no services/DB.
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, existsSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { demoBuildSettings, buildDemoFrontend } from './build_frontend.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = name => readFileSync(path.join(root, name), 'utf8');
const env = { VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: 'https://synthetic-api.example.com', VITE_DEV_MODE: 'false' };

test('separate Vercel config has only declared SPA rewrites and no API proxy', () => {
    const config = JSON.parse(read('demo/vercel.json'));
    const routes = [...read('frontend/src/App.tsx').matchAll(/<Route path="([^"]+)"/g)].map(match => match[1]).filter(route => route !== '*');
    assert.deepEqual(new Set(config.rewrites.map(rule => rule.source)), new Set(routes));
    assert.ok(config.rewrites.every(rule => rule.destination === '/index.html' && !rule.source.startsWith('/api')));
    assert.equal(config.buildCommand, 'node demo/build_frontend.mjs');
    assert.equal(config.outputDirectory, 'frontend/dist-demo');
    assert.ok(!JSON.stringify(config).includes('onrender.com'));
});

test('dedicated frontend rejects missing/disabled demo mode, missing origin and institutional origins', () => {
    for (const invalid of [{ ...env, VITE_FWMS_DEMO_MODE: undefined }, { ...env, VITE_FWMS_DEMO_MODE: 'false' },
        { ...env, VITE_API_URL: undefined }, { ...env, VITE_DEV_MODE: 'true' }]) assert.throws(() => demoBuildSettings(invalid));
    for (const origin of ['https://fwms-workload-system.onrender.com', 'https://FWMS-WORKLOAD-SYSTEM.onrender.com:443/',
        'https://fwms-workload-system.vercel.app', 'https://user:synthetic@demo.example.com', 'https://demo.example.com/api']) {
        assert.throws(() => demoBuildSettings({ ...env, VITE_API_URL: origin }));
    }
});

test('connection policy permits only the explicit demo API origin', () => {
    const config = demoBuildSettings({ ...env, VITE_API_URL: 'http://127.0.0.1:8001/' });
    assert.equal(config.origin, 'http://127.0.0.1:8001');
    assert.equal(config.csp.split(';').find(value => value.trim().startsWith('connect-src')).trim(), 'connect-src http://127.0.0.1:8001');
    assert.ok(!config.csp.includes('onrender.com') && !config.csp.includes('connect-src *'));
});

test('demo image starts only the dedicated launcher and health probe, without institutional artifacts', () => {
    const docker = read('demo/Dockerfile');
    assert.match(docker, /CMD \["python", "demo\/start_backend.py"\]/);
    assert.match(docker, /HEALTHCHECK[^\n]+demo\/healthcheck.py/);
    assert.ok(!/startup\.sh|migrations\/|fixtures\.sql|schema\.sql|\bARG\b|COPY \. /.test(docker));
    const ignore = read('demo/Dockerfile.dockerignore');
    assert.ok(ignore.startsWith('#') && ignore.includes('\n**\n') && ignore.includes('**/.env*'));
    assert.ok(!ignore.includes('!migrations') && !ignore.includes('!startup'));
    assert.match(read('demo/healthcheck.py'), /127\.0\.0\.1:\{port\}\/api\/health/);
    assert.match(read('app/health/router.py'), /prefix="\/api\/health"/);
});

test('demo build refuses an existing directory without deleting or overwriting it', async () => {
    const existing = mkdtempSync(path.join(tmpdir(), 'fwms-demo-existing-'));
    await assert.rejects(buildDemoFrontend(env, existing), /Refusing existing/);
    assert.ok(existsSync(existing));
});

test('real demo build embeds the exact API boundary and never reads Vite env files', async () => {
    const parent = mkdtempSync(path.join(tmpdir(), 'fwms-demo-deployment-build-'));
    const out = path.join(parent, 'site');
    process.env.VITE_UNUSED_SENSITIVE_SETTING = 'synthetic-do-not-embed';
    await buildDemoFrontend(env, out);
    const html = readFileSync(path.join(out, 'index.html'), 'utf8');
    assert.match(html, /http-equiv="Content-Security-Policy"/);
    assert.ok(html.includes('connect-src https://synthetic-api.example.com'));
    const emittedAssets = readdirSync(path.join(out, 'assets'))
        .map(file => readFileSync(path.join(out, 'assets', file), 'utf8')).join('\n');
    assert.ok(emittedAssets.includes('https://synthetic-api.example.com'));
    assert.ok(!emittedAssets.includes('https://fwms-workload-system.onrender.com'));
    assert.equal(process.env.VITE_UNUSED_SENSITIVE_SETTING, undefined);
    assert.match(read('demo/build_frontend.mjs'), /envFile: false/);
    assert.match(read('demo/build_frontend.mjs'), /emptyOutDir: false/);
    console.log('Isolated demo deployment build verified; output is synthetic-only and must not be deployed');
});
