/* Entry-loader tests without a browser or external packages. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/js/entry.js'),'utf8');
async function check(protocol,fail=false) {
  const loaded=[],nodes={};
  for(const id of ['main','nav','#audio-toggle','#theme','.audio-dock'])nodes[id]={hidden:false,replaceChildren(...c){this.children=c;},append(c){this.children.push(c);}};
  nodes['#local-startup']={content:{cloneNode(){return 'startup';}}};
  const document={querySelector:s=>nodes[s],createElement:tag=>({tag}),head:{append(script){loaded.push(script.src);if(fail)script.onerror();else script.onload();}}};
  vm.runInNewContext(source,{document,location:{protocol},Promise,Error});
  await new Promise(resolve=>setImmediate(resolve));
  if(protocol==='file:'){
    assert.deepEqual(loaded,[]);assert.deepEqual(nodes.main.children,['startup']);
    assert.equal(nodes.nav.hidden,true);assert.equal(nodes['.audio-dock'].hidden,true);
  }else if(fail){
    assert.equal(loaded.length,1);assert.match(nodes.main.children[0].textContent,/Extract the complete project/);
  }else assert.deepEqual(loaded,['static/js/audio.js','static/js/app.js']);
}
(async()=>{await check('file:');await check('http:');await check('https:');await check('http:',true);console.log('Entry loader: local-file guidance, HTTP/HTTPS sequencing and missing-file recovery passed.');})().catch(error=>{console.error(error);process.exitCode=1;});
