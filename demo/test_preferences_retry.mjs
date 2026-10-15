// Executes the real TSX component with isolated hooks/API mocks. No network,
// browser storage, database, or preference mutations are allowed.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { createContext, SourceTextModule, SyntheticModule } from 'node:vm';
import { test } from 'node:test';

const require = createRequire(import.meta.url);
const ts = require('../frontend/node_modules/typescript/lib/typescript.js');
const source = readFileSync(fileURLToPath(new URL('../frontend/src/pages/PreferencesPage.tsx', import.meta.url)), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: {
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX,
} }).outputText;
const subjects = ['Synthetic Algorithms', 'Synthetic Database Lab'].map((name, index) => ({
    subject_offering_id: index + 1, course_code: `SYN-${index + 1}`, course_name: name,
    program: 'Synthetic Computing', semester: 'II', section: 'A', shift: 1,
    tch: 4, allocated: false, faculty_name: null, curriculum_year: '2022',
}));
const defaultResponses = {
    getMyPreferences: { data: [] },
    getPreferenceStatus: { data: { total_submitted: 0, remaining: 5, is_complete: false } },
    getPrefWindowStatus: { data: { is_open: false, remaining_seconds: 0 } },
    getSubjectSummary: { data: { records: subjects } },
};
const readNames = Object.keys(defaultResponses);
const tick = () => new Promise(resolve => setImmediate(resolve));
function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    return { promise, resolve, reject };
}
function text(node) {
    if (node == null || typeof node === 'boolean') return '';
    if (Array.isArray(node)) return node.map(text).join(' ');
    if (typeof node === 'object') return text(node.props?.children);
    return String(node);
}
function button(node, label) {
    if (Array.isArray(node)) return node.map(child => button(child, label)).find(Boolean);
    if (!node || typeof node !== 'object') return undefined;
    if (node.type === 'button' && text(node).trim() === label) return node;
    return button(node.props?.children, label);
}

async function mount(overrides = {}) {
    const slots = [], pendingEffects = [], calls = [], notifications = [];
    const responses = { ...defaultResponses, ...overrides };
    let cursor = 0, unmounted = false, writesAfterUnmount = 0;
    const context = createContext({ console: { log() {}, error() {}, warn() {} },
        fetch() { throw new Error('External network forbidden'); },
        localStorage: { getItem() { throw new Error('Storage forbidden'); } },
    });
    const hook = initial => {
        const index = cursor++;
        if (!(index in slots)) slots[index] = initial();
        return index;
    };
    const react = {
        useState(initial) {
            const index = hook(() => ({ value: initial }));
            return [slots[index].value, value => {
                if (unmounted) ++writesAfterUnmount;
                slots[index].value = typeof value === 'function' ? value(slots[index].value) : value;
            }];
        },
        useRef(initial) { return slots[hook(() => ({ current: initial }))]; },
        useMemo(fn) { hook(() => ({})); return fn(); },
        useEffect(fn, deps) {
            const index = hook(() => ({ deps: undefined, cleanup: undefined }));
            const previous = slots[index].deps;
            if (!previous || deps.some((value, i) => value !== previous[i])) {
                slots[index].deps = deps;
                pendingEffects.push(() => { slots[index].cleanup = fn(); });
            }
        },
    };
    const apis = Object.fromEntries(readNames.map(name => [name, () => {
        calls.push(name);
        try { return Promise.resolve(typeof responses[name] === 'function' ? responses[name]() : responses[name]); }
        catch (error) { return Promise.reject(error); }
    }]));
    for (const name of ['submitPreference', 'deletePreference']) apis[name] = () => {
        throw new Error('Preference mutations forbidden');
    };
    const modules = {
        react,
        'react/jsx-runtime': {
            jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }), Fragment: 'fragment',
        },
        '../api/client': apis,
        '../context/AuthContext': { useAuth: () => ({ user: { role: 'faculty', is_demo: true } }) },
        '../hooks/useToast': { useToast: () => ({ toasts: [], removeToast() {},
            addToast(message, type) { notifications.push({ message, type }); },
        }) },
        '../components/ToastContainer': { default: () => null },
        'lucide-react': Object.fromEntries(['Clock', 'AlertCircle', 'RefreshCw', 'Search', 'Filter',
            'BookOpen', 'CheckCircle2', 'XCircle', 'X'].map(name => [name, name])),
    };
    const module = new SourceTextModule(compiled, { context });
    await module.link(name => {
        assert.ok(modules[name], `Unexpected import: ${name}`);
        const exports = modules[name];
        return new SyntheticModule(Object.keys(exports), function () {
            for (const [key, value] of Object.entries(exports)) this.setExport(key, value);
        }, { context });
    });
    await module.evaluate();
    const render = () => {
        cursor = 0;
        const tree = module.namespace.default();
        while (pendingEffects.length) pendingEffects.shift()();
        return tree;
    };
    render();
    await tick();
    return { render, responses, calls, notifications, tick,
        unmount() { unmounted = true; for (const slot of slots) slot.cleanup?.(); },
        get writesAfterUnmount() { return writesAfterUnmount; },
    };
}

test('catalog failure is visible; Retry reloads all four reads and restores subjects', async () => {
    const component = await mount({ getSubjectSummary: () => { throw new Error('Synthetic outage'); } });
    assert.match(text(component.render()), /Could not load subject catalog/);
    component.responses.getSubjectSummary = defaultResponses.getSubjectSummary;
    await button(component.render(), 'Retry').props.onClick();
    const recovered = text(component.render());
    for (const subject of subjects) assert.ok(recovered.includes(subject.course_name));
    assert.ok(!recovered.includes('Please retry'));
    for (const name of readNames) assert.equal(component.calls.filter(call => call === name).length, 2);
    assert.ok(!component.notifications.some(item => item.type === 'success'));
});

test('Retry retains a visible catalog failure when preferences recover but catalog does not', async () => {
    const component = await mount({ getMyPreferences: () => { throw new Error('Offline'); },
        getSubjectSummary: () => { throw new Error('Offline'); } });
    component.responses.getMyPreferences = defaultResponses.getMyPreferences;
    await button(component.render(), 'Retry').props.onClick();
    const tree = component.render();
    assert.match(text(tree), /Could not load subject catalog/);
    assert.ok(button(tree, 'Retry'));
    assert.ok(!text(tree).includes('Loading preferences'));
    assert.ok(!component.notifications.some(item => item.type === 'success'));
});

test('Retry retains preference failure when the catalog recovers', async () => {
    const component = await mount({ getMyPreferences: () => { throw new Error('Offline'); } });
    await button(component.render(), 'Retry').props.onClick();
    assert.match(text(component.render()), /Could not connect to server/);
    assert.ok(button(component.render(), 'Retry'));
});

test('Retry shows loading until preference reads settle', async () => {
    const component = await mount({ getSubjectSummary: () => { throw new Error('Offline'); } });
    const waiting = deferred();
    component.responses.getMyPreferences = () => waiting.promise;
    component.responses.getSubjectSummary = defaultResponses.getSubjectSummary;
    const retry = button(component.render(), 'Retry').props.onClick();
    assert.match(text(component.render()), /Loading preferences/);
    waiting.resolve(defaultResponses.getMyPreferences);
    await retry;
    assert.match(text(component.render()), /Synthetic Algorithms/);
});

test('catalog loading does not masquerade as an empty catalog or complete recovery', async () => {
    const component = await mount({ getSubjectSummary: () => { throw new Error('Offline'); } });
    const waiting = deferred();
    component.responses.getSubjectSummary = () => waiting.promise;
    const retry = button(component.render(), 'Retry').props.onClick();
    await tick();
    const loading = text(component.render());
    assert.match(loading, /Loading subject catalog/);
    assert.ok(!loading.includes('No subjects match'));
    waiting.reject(new Error('Still offline'));
    await retry;
    assert.match(text(component.render()), /Could not load subject catalog/);
});

test('older catalog failure cannot replace newer catalog success', async () => {
    const stale = deferred();
    const component = await mount({ getMyPreferences: () => { throw new Error('Offline'); },
        getSubjectSummary: () => stale.promise });
    component.responses.getMyPreferences = defaultResponses.getMyPreferences;
    component.responses.getSubjectSummary = defaultResponses.getSubjectSummary;
    await button(component.render(), 'Retry').props.onClick();
    stale.reject(new Error('Obsolete failure'));
    await tick();
    assert.match(text(component.render()), /Synthetic Algorithms/);
    assert.ok(!text(component.render()).includes('Could not load subject catalog'));
});

test('obsolete preference results cannot clear latest loading or overwrite newer state', async () => {
    const stale = deferred(), current = deferred();
    const component = await mount({ getMyPreferences: () => stale.promise,
        getSubjectSummary: () => { throw new Error('Offline'); } });
    // Settle initial data as failure to expose Retry, then start two overlapping
    // invocations of the real handler before React can disable the old button.
    stale.reject(new Error('Offline'));
    await tick();
    const retryButton = button(component.render(), 'Retry');
    const older = deferred();
    component.responses.getMyPreferences = () => older.promise;
    component.responses.getSubjectSummary = defaultResponses.getSubjectSummary;
    const first = retryButton.props.onClick();
    component.responses.getMyPreferences = () => current.promise;
    const second = retryButton.props.onClick();
    older.resolve(defaultResponses.getMyPreferences);
    await first;
    assert.match(text(component.render()), /Loading preferences/);
    current.resolve(defaultResponses.getMyPreferences);
    await second;
    assert.match(text(component.render()), /Synthetic Algorithms/);
});

test('obsolete catalog success cannot overwrite a newer catalog', async () => {
    const stale = deferred();
    const component = await mount({ getMyPreferences: () => { throw new Error('Offline'); },
        getSubjectSummary: () => stale.promise });
    component.responses.getMyPreferences = defaultResponses.getMyPreferences;
    component.responses.getSubjectSummary = defaultResponses.getSubjectSummary;
    await button(component.render(), 'Retry').props.onClick();
    stale.resolve({ data: { records: [{ ...subjects[0], course_name: 'Obsolete Subject' }] } });
    await tick();
    assert.match(text(component.render()), /Synthetic Algorithms/);
    assert.ok(!text(component.render()).includes('Obsolete Subject'));
});

test('pending preference/catalog reads do not update state after unmount', async () => {
    const prefs = deferred(), catalog = deferred();
    const component = await mount({ getMyPreferences: () => prefs.promise, getSubjectSummary: () => catalog.promise });
    component.unmount();
    prefs.resolve(defaultResponses.getMyPreferences);
    catalog.reject(new Error('Offline after unmount'));
    await tick();
    assert.equal(component.writesAfterUnmount, 0);
    assert.equal(component.notifications.length, 0);
});
