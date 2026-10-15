// Safe verification only: no .env loading, no existing dist/build-info writes.
import {createRequire} from 'node:module';
import {mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=fileURLToPath(new URL('../',import.meta.url));
process.chdir(root);
const require=createRequire(path.resolve('frontend/package.json'));
const ts=require('../frontend/node_modules/typescript/lib/typescript.js');
for (const name of ['tsconfig.app.json','tsconfig.node.json']) {
    const configPath=path.resolve('frontend',name),directory=path.dirname(configPath);
    const config=ts.readConfigFile(configPath,ts.sys.readFile);
    const parsed=ts.parseJsonConfigFileContent(config.config,ts.sys,directory,undefined,configPath);
    const options={...parsed.options,noEmit:true,incremental:false};
    delete options.tsBuildInfoFile;
    const host=ts.createCompilerHost(options);
    host.getCurrentDirectory=()=>directory;
    host.writeFile=()=>{throw new Error('Emission forbidden');};
    const program=ts.createProgram(parsed.fileNames,options,host);
    const diagnostics=[...parsed.errors,...ts.getPreEmitDiagnostics(program)];
    console.log(name+': '+diagnostics.length+' diagnostics');
    if(diagnostics.length) {
        console.log(diagnostics.map(d=>({code:d.code,file:d.file?.fileName,
            line:d.file&&d.start!==undefined?d.file.getLineAndCharacterOfPosition(d.start).line+1:undefined})));
        process.exit(1);
    }
}
const {build}=await import(pathToFileURL(require.resolve('vite')));
const {default:react}=await import(pathToFileURL(require.resolve('@vitejs/plugin-react')));
const {default:tailwindcss}=await import(pathToFileURL(require.resolve('@tailwindcss/vite')));
for(const key of Object.keys(process.env)) if(key.startsWith('VITE_')) delete process.env[key];
process.env.VITE_API_URL='http://localhost:8001';
process.env.VITE_FWMS_DEMO_MODE='true';
process.env.VITE_DEV_MODE='false';
const outDir=mkdtempSync(path.join(tmpdir(),'fwms-demo-build-'));
console.log('Synthetic-only verification output (DO NOT DEPLOY): '+outDir);
// Matches the current Vite plugin list. Config-file loading is deliberately
// bypassed to avoid creating configuration cache files in the working tree.
await build({configFile:false,envFile:false,root:path.resolve('frontend'),
    plugins:[react(),tailwindcss()],mode:'production',build:{outDir,emptyOutDir:false}});
