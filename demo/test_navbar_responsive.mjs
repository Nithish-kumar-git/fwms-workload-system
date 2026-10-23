// Guards the responsive containment added after the live 390px overflow finding.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

const source = readFileSync(fileURLToPath(new URL('../frontend/src/components/Navbar.tsx', import.meta.url)), 'utf8');

test('navbar contains role links and account controls at mobile widths', () => {
    assert.match(source, /flex flex-col gap-2[\s\S]*sm:flex-row/);
    assert.match(source, /min-w-0 flex-1[\s\S]*overflow-x-auto[\s\S]*sm:overflow-visible/);
    assert.match(source, /border-t border-gray-100[\s\S]*sm:border-0/);
    assert.match(source, /min-w-0 truncate text-\[12px\]/);
});
