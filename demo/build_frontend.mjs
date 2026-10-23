// Dedicated demo build only. No .env loading or institutional build output writes.
import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const require = createRequire(path.join(root, 'frontend/package.json'));

export function demoBuildSettings(env) {
    if (env.VITE_FWMS_DEMO_MODE !== 'true') throw new Error('Dedicated build requires VITE_FWMS_DEMO_MODE=true');
    if (!env.VITE_API_URL) throw new Error('Dedicated build requires VITE_API_URL');
    if (env.VITE_DEV_MODE && env.VITE_DEV_MODE !== 'false') throw new Error('Dedicated build forbids development authentication');
    let url;
    try { url = new URL(env.VITE_API_URL); } catch { throw new Error('Invalid dedicated demo API origin'); }
    if (url.username || url.password || url.search || url.hash || !['', '/'].includes(url.pathname) ||
        !(url.protocol === 'https:' || (url.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname))) ||
        ['fwms-workload-system.onrender.com', 'fwms-workload-system.vercel.app'].includes(url.hostname)) {
        throw new Error('Dedicated demo requires a separate API origin');
    }
    return { origin: url.origin, csp: `default-src 'self'; connect-src ${url.origin}; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'none'` };
}

export async function buildDemoFrontend(env = process.env, outDir = path.join(root, 'frontend/dist-demo')) {
    const configuration = demoBuildSettings(env);
    outDir = path.resolve(outDir);
    if (outDir === path.join(root, 'frontend/dist') || existsSync(outDir)) {
        throw new Error('Refusing existing or institutional output directory; use a fresh build workspace');
    }
    // Expose only the public demo configuration, never arbitrary VITE_* secrets.
    for (const key of Object.keys(process.env)) if (key.startsWith('VITE_')) delete process.env[key];
    Object.assign(process.env, { VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: configuration.origin, VITE_DEV_MODE: 'false' });
    const { build } = await import(pathToFileURL(require.resolve('vite')));
    const { default: react } = await import(pathToFileURL(require.resolve('@vitejs/plugin-react')));
    const { default: tailwind } = await import(pathToFileURL(require.resolve('@tailwindcss/vite')));
    await build({ configFile: false, envFile: false, root: path.join(root, 'frontend'),
        define: { __FWMS_DEMO_BUILD__: 'true' },
        plugins: [react(), tailwind(), { name: 'demo-api-boundary', transformIndexHtml() {
            return [{ tag: 'meta', attrs: { 'http-equiv': 'Content-Security-Policy', content: configuration.csp }, injectTo: 'head-prepend' }];
        } }], mode: 'production', build: { outDir, emptyOutDir: false },
    });
    return outDir;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    try {
        const args = process.argv.slice(2);
        if (args.length && (args.length !== 2 || args[0] !== '--out-dir')) throw new Error('Expected --out-dir with a fresh directory');
        await buildDemoFrontend(process.env, args[1]);
        console.log('Dedicated synthetic frontend build completed');
    } catch {
        // Do not echo supplied configuration or build exceptions containing it.
        console.error('Dedicated demo build failed. Check required public demo configuration and build prerequisites.');
        process.exitCode = 1;
    }
}
