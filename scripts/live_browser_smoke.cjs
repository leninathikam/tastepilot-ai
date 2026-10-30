// Explicitly invoked live smoke. Saves only counts/status, never API responses or keys.
const {chromium}=require('../frontend/node_modules/@playwright/test');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch();
 try {
  const mobile=process.argv.includes('--mobile');
  const page=await browser.newPage(mobile?{viewport:{width:390,height:844},isMobile:true,hasTouch:true}:{});
  await page.goto('http://127.0.0.1:3000');
  await page.getByRole('button',{name:'Add companion',exact:true}).click();
  const responsePromise=page.waitForResponse(r=>r.url().endsWith('/api/plan'),{timeout:70000});
  await page.getByRole('button',{name:'Build my day'}).click();
  const response=await responsePromise;
  const events=(await response.text()).trim().split('\n').map(JSON.parse);
  const result=events.find(e=>e.type==='result');
  if(!result)throw Error(events.find(e=>e.type==='error')?.message||'Missing result');
  if(result.mode!=='live'||!result.group||!result.group.selected_ids.length)throw Error('Expected nonempty live group discoveries');
  await page.getByRole('heading',{name:'A day everyone has a part in.'}).waitFor();
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(overflow)throw Error('Horizontal overflow');
  const status={checked_at:new Date().toISOString(),passed:true,mode:result.mode,qloo_calls:result.metrics.qloo_calls,candidates:result.metrics.candidate_count,group_profiles:result.group.modeled_profiles,provisional_group_choices:result.group.selected_ids.length,confirmed_stops:result.itinerary.length,budget_complete:result.budget.complete,source:result.provenance.source,raw_responses_saved:false};
  status.viewport=mobile?'mobile':'desktop';
  fs.writeFileSync(`evaluation/results/live_browser_${mobile?'mobile':'desktop'}_status.json`,JSON.stringify(status,null,2));console.log(JSON.stringify(status,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
