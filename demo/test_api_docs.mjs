// Real Navbar + API configuration, transpiled in memory. No network or storage.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { createContext, SourceTextModule, SyntheticModule } from 'node:vm';
import { test } from 'node:test';

const require = createRequire(import.meta.url);
const ts = require('../frontend/node_modules/typescript/lib/typescript.js');
const compile = relative => ts.transpileModule(readFileSync(fileURLToPath(new URL(relative, import.meta.url)), 'utf8'), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX },
}).outputText;
const navbarSource = compile('../frontend/src/components/Navbar.tsx');
const clientSource = compile('../frontend/src/api/client.ts');
const institutional = 'https://fwms-workload-system.onrender.com/docs';

function docsLink(node) {
    if (Array.isArray(node)) return node.map(docsLink).find(Boolean);
    if (!node || typeof node !== 'object') return undefined;
    if (node.type === 'a' && node.props.title === 'View API documentation (Swagger)') return node;
    return docsLink(node.props?.children);
}
async function render(environment, role = 'faculty') {
    const forbidden = () => { throw new Error('Network/storage/mutation forbidden'); };
    const context = createContext({ URL, URLSearchParams, console, fetch: forbidden,
        localStorage: { getItem: forbidden, setItem: forbidden, removeItem: forbidden },
    });
    const client = new SourceTextModule(clientSource, { context,
        initializeImportMeta(meta) { meta.env = environment; },
    });
    await client.link(name => {
        assert.equal(name, 'axios');
        return new SyntheticModule(['default'], function () {
            this.setExport('default', { create() { return { get: forbidden, post: forbidden,
                interceptors: { request: { use() {} }, response: { use() {} } },
            }; } });
        }, { context });
    });
    await client.evaluate();
    const modules = {
        'react-router-dom': { Link: 'Link', useLocation: () => ({ pathname: '/preferences' }), useNavigate: () => forbidden },
        'react/jsx-runtime': { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }) },
        '../context/AuthContext': { useAuth: () => ({ user: { name: 'Synthetic User', role } }) },
        'lucide-react': Object.fromEntries(['LayoutDashboard', 'BookOpen', 'Settings', 'FileText', 'LogOut',
            'Clock', 'CalendarDays', 'Users', 'Shield', 'Upload', 'CheckCircle', 'ClipboardList',
            'ExternalLink'].map(name => [name, name])),
    };
    const navbar = new SourceTextModule(navbarSource, { context });
    await navbar.link(name => {
        if (name === '../api/client') return client;
        assert.ok(modules[name], `Unexpected import: ${name}`);
        const exports = modules[name];
        return new SyntheticModule(Object.keys(exports), function () {
            for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
        }, { context });
    });
    await navbar.evaluate();
    return docsLink(navbar.namespace.default());
}

test('demo Docs link uses configured backend /docs for all supported roles', async () => {
    for (const role of ['hod', 'tt_coordinator', 'faculty']) {
        const link = await render({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: 'https://synthetic-api.example.com' }, role);
        assert.equal(link.props.href, 'https://synthetic-api.example.com/docs');
        assert.notEqual(link.props.href, institutional);
        assert.equal(link.props.target, '_blank');
        assert.equal(link.props.rel, 'noopener noreferrer');
    }
});

test('demo localhost and trailing-slash configuration never use a production fallback', async () => {
    for (const origin of ['http://localhost:8001', 'http://127.0.0.1:8001/', 'http://[::1]:8001/']) {
        const link = await render({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: origin });
        assert.equal(link.props.href, new URL('/docs', origin).href);
        assert.notEqual(link.props.href, institutional);
    }
});

test('demo hides Docs link even if configured with the known institutional backend', async () => {
    for (const origin of ['https://fwms-workload-system.onrender.com',
        'https://fwms-workload-system.onrender.com/', 'https://FWMS-WORKLOAD-SYSTEM.onrender.com:443/']) {
        assert.equal(await render({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: origin }), undefined);
    }
});

test('missing or invalid demo API configuration fails closed rather than rendering production Docs', async () => {
    for (const origin of [undefined, 'http://public.example.com', 'https://synthetic-api.example.com/api',
        'https://user:synthetic@synthetic-api.example.com']) {
        await assert.rejects(render({ VITE_FWMS_DEMO_MODE: 'true', VITE_API_URL: origin }));
    }
});

test('institutional Docs destination remains unchanged', async () => {
    for (const environment of [{}, { VITE_FWMS_DEMO_MODE: 'false', VITE_API_URL: 'https://other.example.com' }]) {
        assert.equal((await render(environment)).props.href, institutional);
    }
});
