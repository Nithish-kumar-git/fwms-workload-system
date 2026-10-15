// Actual AllocationPage TSX with mocked reads/actions. No network, storage or DB writes.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { createContext, SourceTextModule, SyntheticModule } from 'node:vm';
import { test } from 'node:test';

const require = createRequire(import.meta.url);
const ts = require('../frontend/node_modules/typescript/lib/typescript.js');
const source = readFileSync(fileURLToPath(new URL('../frontend/src/pages/AllocationPage.tsx', import.meta.url)), 'utf8');
const fixtureSql = readFileSync(fileURLToPath(new URL('./fixtures.sql', import.meta.url)), 'utf8');
const fixtureName = /INSERT INTO program\(name,ug_pg\) VALUES \('([^']+)'/.exec(fixtureSql)?.[1];
assert.ok(fixtureName, 'Synthetic fixture program name must be discoverable');
const compiled = ts.transpileModule(source, { compilerOptions: {
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX,
} }).outputText;
const tick = () => new Promise(resolve => setImmediate(resolve));
function text(node) {
    if (node == null || typeof node === 'boolean') return '';
    if (Array.isArray(node)) return node.map(text).join(' ');
    return typeof node === 'object' ? text(node.props?.children) : String(node);
}
function nodes(node, predicate) {
    if (Array.isArray(node)) return node.flatMap(child => nodes(child, predicate));
    if (!node || typeof node !== 'object') return [];
    return [...(predicate(node) ? [node] : []), ...nodes(node.props?.children, predicate)];
}
const options = tree => nodes(tree, node => node.type === 'option')
    .map(node => ({ value: String(node.props.value), label: text(node) }));

async function mount(mode, programs = [{ id: 37, name: fixtureName, ug_pg: 'UG' }]) {
    const slots = [], calls = [], effects = [], notices = [];
    let cursor = 0, disposed = false, writesAfterUnmount = 0;
    const context = createContext({ console,
        fetch() { throw new Error('External network forbidden'); },
        localStorage: { getItem() { throw new Error('Storage forbidden'); } },
    });
    const modules = {
        react: {
            useState(initial) {
                const index = cursor++;
                if (!(index in slots)) slots[index] = { value: initial };
                return [slots[index].value, value => {
                    if (disposed) ++writesAfterUnmount;
                    slots[index].value = typeof value === 'function' ? value(slots[index].value) : value;
                }];
            },
            useEffect(fn) {
                const index = cursor++;
                if (!(index in slots)) { slots[index] = {}; effects.push(() => { slots[index].cleanup = fn(); }); }
            },
        },
        'react/jsx-runtime': { jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }), Fragment: 'fragment' },
        '../hooks/useToast': { useToast: () => ({ toasts: [], removeToast() {}, addToast(message) { notices.push(message); } }) },
        '../components/ToastContainer': { default: () => null },
        'lucide-react': Object.fromEntries(['Play', 'CheckCircle', 'AlertTriangle', 'AlertCircle', 'Calendar', 'Zap'].map(name => [name, name])),
        '../api/client': {
            getActiveCycle() { calls.push({ name: 'cycle' }); return Promise.resolve({ data: { academic_year: '2026-2027', semester_id: 2 } }); },
            getSubjectPrograms() {
                calls.push({ name: 'programs' });
                if (programs instanceof Error) return Promise.reject(programs);
                return programs?.then ? programs : Promise.resolve({ data: programs });
            },
            runAllocation(payload) {
                // Capture the real component's scope payload; never execute an allocation.
                calls.push({ name: 'single', payload });
                return Promise.resolve({ data: { success: true, subjects_total: 0,
                    subjects_assigned: 0, subjects_unassigned: 0, faculty_overloaded: 0,
                    faculty_underloaded: 0, faculty_balanced: 0, allocations: [], unallocated: [],
                } });
            },
            runAllocationForAllSemesters() { throw new Error('Run All must not be invoked by filter tests'); },
        },
    };
    const module = new SourceTextModule(compiled, { context, initializeImportMeta(meta) { meta.env = { VITE_FWMS_DEMO_MODE: mode }; } });
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
        while (effects.length) effects.shift()();
        return tree;
    };
    render();
    await tick();
    return { render, calls, notices,
        async select(value) { nodes(render(), node => node.type === 'select')[0].props.onChange({ target: { value } }); },
        async run() { await nodes(render(), node => node.type === 'button' && text(node).includes('Run Single Semester'))[0].props.onClick(); },
        unmount() { disposed = true; for (const slot of slots) slot.cleanup?.(); },
        get writesAfterUnmount() { return writesAfterUnmount; },
    };
}

test('demo options use the actual fixture program name and backend ID, not MCA/BCA or assumed IDs', async () => {
    const component = await mount('true');
    assert.deepEqual(options(component.render()), [
        { value: '', label: 'All Programs (Entire Cycle)' }, { value: '37', label: fixtureName },
    ]);
    assert.equal(component.calls.filter(call => call.name === 'programs').length, 1);
    await component.select('37');
    await component.run();
    const payload = component.calls.find(call => call.name === 'single').payload;
    assert.equal(payload.program_id, 37);
    assert.equal(payload.academic_year, '2026-2027');
    assert.equal(payload.semester_id, 2);
});

test('demo All Programs retains null scope rather than an invented program', async () => {
    const component = await mount('true');
    await component.select('37');
    await component.select('');
    await component.run();
    assert.equal(component.calls.find(call => call.name === 'single').payload.program_id, null);
});

test('institutional labels, IDs and all-program scope remain unchanged without extra program reads', async () => {
    for (const mode of [undefined, 'false']) {
        const component = await mount(mode, new Error('Institutional program read should not happen'));
        assert.deepEqual(options(component.render()), [
            { value: '', label: 'All Programs (Entire Cycle)' }, { value: '1', label: 'MCA' }, { value: '2', label: 'BCA' },
        ]);
        assert.ok(!component.calls.some(call => call.name === 'programs'));
        for (const [value, expected] of [['1', 1], ['2', 2], ['', null]]) {
            await component.select(value);
            await component.run();
            assert.equal(component.calls.filter(call => call.name === 'single').at(-1).payload.program_id, expected);
        }
    }
});

test('failed demo program metadata shows an error, never institutional fallback options', async () => {
    const component = await mount('true', new Error('Synthetic outage'));
    assert.match(text(component.render()), /Failed to load demo program filters/);
    assert.equal(options(component.render()).length, 0);
    assert.equal(nodes(component.render(), node => node.type === 'button').length, 0);
});

test('malformed program metadata fails safely; empty valid dataset does not invent options', async () => {
    for (const invalid of [null, {}, [{ id: '1', name: fixtureName }], [{ id: 1, name: '' }]]) {
        const component = await mount('true', invalid);
        assert.match(text(component.render()), /Failed to load demo program filters/);
        assert.equal(options(component.render()).length, 0);
    }
    const empty = await mount('true', []);
    assert.deepEqual(options(empty.render()), [{ value: '', label: 'All Programs (Entire Cycle)' }]);
});

test('pending demo program reads do not update an unmounted page', async () => {
    let resolve;
    const pending = new Promise(done => { resolve = done; });
    const component = await mount('true', pending);
    component.unmount();
    resolve({ data: [{ id: 37, name: fixtureName }] });
    await tick();
    assert.equal(component.writesAfterUnmount, 0);
});
