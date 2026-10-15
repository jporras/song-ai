// Run with Playwright MCP against isolated QA. No inference or generation.
async page => {
  const results = [];
  for (const phase of ['intent','instrumental','music-plan','lyrics','production:5. Revisar','production:6. Generar','production:7. Studio','voice','library']) {
    await page.goto('http://127.0.0.1:8024/' + phase.split(':')[0]);
    await page.waitForFunction(() => document.querySelector('#app')?.__vue_app__?._container?._vnode?.component?.proxy.activeProject?.music_spec_revision_id);
    if (phase.includes(':')) {
      await page.waitForFunction(() => Boolean(document.querySelector('#app').__vue_app__._container._vnode.component.proxy.activeProfessionalProject));
      await page.getByRole('button',{name:phase.split(':')[1],exact:true}).click();
      if (phase.endsWith('Revisar')) await page.getByRole('button',{name:'Configurar accion sobre el audio',exact:true}).click();
    }
    // Open help and family surfaces without editing the project.
    await page.locator('main details').evaluateAll(es => es.forEach(e => e.open = true));
    const result = await page.evaluate(() => {
      const rgba = s => { const v=(s.match(/[\d.]+/g)||[]).map(Number); return [v[0]||0,v[1]||0,v[2]||0,v[3] ?? 1]; };
      const blend = (a,b) => [0,1,2].map(i => a[i]*a[3]+b[i]*(1-a[3])).concat(1);
      const background = e => { const chain=[]; for(let p=e;p;p=p.parentElement)chain.unshift(p); return chain.reduce((b,p)=>blend(rgba(getComputedStyle(p).backgroundColor),b),[16,19,27,1]); };
      const luminance = c => c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
      const ratio = (a,b) => (Math.max(luminance(a),luminance(b))+.05)/(Math.min(luminance(a),luminance(b))+.05);
      const rows=[];
      for(const e of document.querySelectorAll('main input,main select,main textarea,.gemma-footer textarea')) {
        if(!e.getClientRects().length||e.disabled||['range','checkbox','radio','hidden','file'].includes(e.type))continue;
        const c=getComputedStyle(e), bg=background(e), outside=background(e.parentElement);
        const border=rgba(c.borderTopColor);
        const row={name:e.getAttribute('aria-label')||e.closest('label')?.textContent.trim().slice(0,50)||e.id, border:Math.min(ratio(blend(border,bg),bg),ratio(blend(border,outside),outside)), text:ratio(blend(rgba(c.color),bg),bg)};
        if(e.hasAttribute('placeholder'))row.placeholder=ratio(blend(rgba(getComputedStyle(e,'::placeholder').color),bg),bg);
        rows.push(row);
      }
      return {count:rows.length,minBorder:Math.min(...rows.map(r=>r.border)),minText:Math.min(...rows.map(r=>r.text)),placeholders:rows.filter(r=>r.placeholder!==undefined),failures:rows.filter(r=>r.border<3||r.text<4.5||(r.placeholder!==undefined&&r.placeholder<4.5))};
    });
    results.push({phase,...result});
  }
  if(results.some(r=>r.failures.length))throw Error(JSON.stringify(results));
  return results;
}
