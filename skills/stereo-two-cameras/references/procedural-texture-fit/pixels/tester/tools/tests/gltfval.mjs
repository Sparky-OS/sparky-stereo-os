// The Khronos glTF-Validator over a scene folder: gltfval.mjs VALIDATOR-PACKAGE-DIR SCENE.gltf OUT.json
// Prints the counts and every message; exit 1 on any error or warning.
import { createRequire } from 'node:module';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
const [pkg, scene, out] = process.argv.slice(2);
const validator = createRequire(import.meta.url)(path.resolve(pkg, 'package'));
const dir = path.dirname(path.resolve(scene));
const bytes = new Uint8Array(await readFile(scene));
const report = await validator.validateBytes(bytes, {
  uri: path.basename(scene),
  externalResourceFunction: async (uri) => new Uint8Array(await readFile(path.join(dir, decodeURIComponent(uri)))),
});
await writeFile(out, JSON.stringify(report, null, 1));
const i = report.issues;
console.log(`validator ${report.validatorVersion}: ${i.numErrors} errors, ${i.numWarnings} warnings, ${i.numInfos} infos, ${i.numHints} hints`);
for (const m of i.messages) console.log(`  ${['error', 'warning', 'info', 'hint'][m.severity]} ${m.code} ${m.pointer || ''}: ${m.message}`);
console.log(`  extensionsUsed: ${report.info.extensionsUsed}; images ${report.info.resources.filter((r) => r.image).length}`);
process.exit(i.numErrors || i.numWarnings ? 1 : 0);
