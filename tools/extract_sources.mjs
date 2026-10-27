// Development-only conversion. Executes only the vendored, reviewed TS data modules.
// The installed Python package never executes or imports upstream JavaScript.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../isla_questionnaires/data/sources');
const read = p => fs.readFileSync(path.join(root,p), 'utf8');
const out = {};
for (const file of fs.readdirSync(path.join(root,'psyche/web/src/instruments')).filter(f=>f.endsWith('.ts'))) {
  let captured;
  let src = read('psyche/web/src/instruments/'+file).replace(/^import .*?;\s*$/gm,'').replace(/^export default .*?;\s*$/gm,'').replace(/^export /gm,'');
  const ctx = {registerInstrument: d=>{captured=d;}, scoreLikert:()=>{}, scoreBinary:()=>{}};
  vm.runInNewContext(stripTypeScriptTypes(src), ctx, {timeout:2000});
  out[file.slice(0,-3)] = captured;
}
let src = read('bigfive-web/packages/questions/src/data/en/questions.ts').replace(/^import .*?;?\s*$/gm,'').replace(/export default questions;?/, 'globalThis.result = questions;');
let ctx = {};
vm.runInNewContext(stripTypeScriptTypes(src),ctx,{timeout:2000}); out.bigfive = ctx.result;
src = read('pvq-rr/index.html');
src = src.slice(src.indexOf('const pronounMaps'),src.indexOf('const labels1to6')) + src.match(/const labels1to6[^;]+;/)[0];
ctx={}; vm.runInNewContext(src+';globalThis.result={pronounMaps,baseItems,valueMeta,labels1to6};',ctx,{timeout:2000});out.pvqrr=ctx.result;
src=read('health-habit-hub/app/utils/srhi.js').replace(/export const /g,'const ');
ctx={};vm.runInNewContext(src+';globalThis.result=SRHI_ITEMS;',ctx,{timeout:2000});out.srhi=ctx.result;
src=read('psv/04_code_and_reproducibility/procedure/day1/surveys/selfclarity.js');
ctx={jsPsychSurveyTemplate:'survey'};vm.runInNewContext(src+';globalThis.result=selfclarity;',ctx,{timeout:2000});out.scc=ctx.result;
fs.writeFileSync(path.join(root,'extracted.json'),JSON.stringify(out,null,2)+'\n');
console.log(Object.fromEntries(Object.entries(out).map(([k,v])=>[k, v?.items?.length ?? v?.length ?? Object.keys(v??{})])));
