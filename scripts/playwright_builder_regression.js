// Playwright MCP browser_run_code_unsafe filename. Run against an isolated QA
// server with a project loaded. Does not request inference or generation.
async (page) => {
  const guards = await page.evaluate(() => {
    const computed = document.querySelector('#app').__vue_app__._component.computed;
    const results = [];
    for (const phase of ['MASTERING', 'EXPORT']) {
      for (const confirmed of [true, false]) {
        const context = {
          productionPipelineSteps: [{phase, requires:'qa', summary:'qa', action:'qa'}],
          activeProfessionalProject: {current_phase:phase, status:'waiting', events:[], artifacts:[]},
          exportManifest:null, productionRunningPhase:'',
          specificationRevision:{user_confirmation_status:confirmed ? 'confirmed' : 'pending'},
        };
        Object.defineProperty(context, 'sampleCheckpointStatus', {
          get() { throw Error('Optional sample must not gate full generation or export'); },
        });
        const step = computed.productionProcessSteps.call(context)[0];
        if (step.canRun !== confirmed) throw Error('Configuration confirmation guard changed');
        results.push({phase, confirmed, canRun:step.canRun});
      }
    }
    return results;
  });
  const navigation = [];
  for (const name of ['1. Idea','2. Sonido','3. Composición','4. Estructura y letra','5. Revisar','6. Generar','7. Studio']) {
    const saved = page.waitForResponse(response => response.url().includes('/ui-state')
      && response.request().method() === 'PUT'
      && JSON.parse(response.request().postData() || '{}').builder_step ===
        ({'1. Idea':'idea','2. Sonido':'sound','3. Composición':'composition','4. Estructura y letra':'lyrics','5. Revisar':'review','6. Generar':'generate','7. Studio':'studio'})[name]);
    await page.getByRole('button', {name, exact:true}).click();
    if ((await saved).status() !== 200) throw Error('Navigation state was not persisted');
    await page.getByRole('button', {name, exact:true}).evaluate(e => {
      if (e.getAttribute('aria-current') !== 'step') throw Error('Builder navigation did not finish');
    });
    for (const width of [390,768,1440]) {
      await page.setViewportSize({width, height:900});
      const size = await page.evaluate(() => ({width:innerWidth, scroll:document.documentElement.scrollWidth}));
      if (size.scroll > size.width + 1) throw Error(`Horizontal overflow: ${name} at ${width}`);
      navigation.push({step:name, ...size});
    }
  }
  await page.reload();
  await page.getByRole('heading', {name:'Studio', exact:true}).waitFor();
  await page.getByRole('button', {name:'7. Studio', exact:true}).evaluate(e => {
    if (e.getAttribute('aria-current') !== 'step') throw Error('Studio was not restored');
  });
  await page.getByRole('button', {name:'5. Revisar', exact:true}).click();
  const help = page.locator('.builder-project-summary summary').first();
  await help.focus();
  await page.keyboard.press('Enter');
  const keyboardHelp = await help.evaluate(e => ({open:e.parentElement.open, focused:e === document.activeElement, outline:getComputedStyle(e).outlineStyle}));
  if (!keyboardHelp.open || !keyboardHelp.focused || keyboardHelp.outline === 'none') throw Error('Keyboard help unavailable');
  const text = await page.locator('main').innerText();
  if (/Revisión corta obligatoria|plan musical y MIDI editable|Intent → Lyrics → Music Plan → MIDI/i.test(text)) throw Error('Outdated required steps remain visible');
  return {guards, navigation, studioReload:true, keyboardHelp, scope:'QA UI/backend; guard uses computed function with fixtures; no inference/audio'};
}
