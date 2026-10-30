// Opt-in real UI rehearsal. Public URL supplied only after owner deployment.
const {chromium}=require('../frontend/node_modules/@playwright/test');
const fs=require('node:fs');
const base=process.env.JUDGE_BASE_URL||'http://127.0.0.1:3000';
(async()=>{
 const browser=await chromium.launch();
 const directory='docs/screenshots';fs.mkdirSync(directory,{recursive:true});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.addInitScript(()=>{window.__judgePlans=[];const original=window.fetch.bind(window);window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).endsWith('/api/plan'))response.clone().text().then(text=>window.__judgePlans.push(text));return response;};});
  const home=await page.goto(base);if(!home.ok())throw Error('Home did not load');
  await page.locator('.hero img').first().waitFor();
  await page.locator('.hero').screenshot({path:`${directory}/01-landing.png`});
  await page.getByRole('button',{name:'Try the four-person example'}).click();
  await page.locator('.group-profiles').screenshot({path:`${directory}/02-profiles.png`});
  await page.getByRole('button',{name:'Build my day'}).click();
  await page.waitForFunction(()=>window.__judgePlans.length>=1,{},{timeout:70000});
  const events=(await page.evaluate(()=>window.__judgePlans[0])).trim().split('\n').map(JSON.parse);
  const result=events.find(e=>e.type==='result');
  if(!result||result.mode!=='live'||result.group.modeled_profiles!==4)throw Error('Expected real four-profile result');
  await page.locator('.tradeoff-table').waitFor();
  await page.locator('.group-report').screenshot({path:`${directory}/03-compromise.png`});
  const first=page.locator('.stop').first();
  await first.locator('summary').first().click();
  await first.screenshot({path:`${directory}/04-evidence.png`});
  await page.setViewportSize({width:390,height:844});
  await page.locator('.group-report').screenshot({path:`${directory}/05-mobile.png`});
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
  await page.getByLabel('Require step-free access for Alex').check();
  await page.getByRole('button',{name:'Build my day'}).click();
  await page.waitForFunction(()=>window.__judgePlans.length>=2,{},{timeout:70000});
  const revised=(await page.evaluate(()=>window.__judgePlans[1])).trim().split('\n').map(JSON.parse).find(e=>e.type==='result');
  if(!revised||revised.itinerary.length||revised.alternatives.length)throw Error('Unknown accessibility bypassed');
  const invalid=await page.request.post(`${base}/api/plan`,{data:{date:'2026-10-31',budget:-1}});
  if(invalid.status()!==422)throw Error('Invalid input accepted');
  const status={checked_at:new Date().toISOString(),base_url:base,public_verified:!base.includes('127.0.0.1')&&!base.includes('localhost'),four_profile_workflow:true,
   qloo_calls:result.metrics.qloo_calls,candidates:result.metrics.candidate_count,choices:result.group.selected_ids.length,
   minimum_coverage_delta:result.group.minimum_coverage_delta,mean_coverage_tradeoff:result.group.mean_coverage_tradeoff,
   objectives_differ:JSON.stringify([...result.group.selected_ids].sort())!==JSON.stringify([...result.group.mean_objective.ids].sort()),
   member_coverage:{fair:result.group.fair.member_coverage,mean:result.group.mean_objective.member_coverage},
   unknown_access_rejected:true,invalid_input_rejected:true,mobile_overflow:false,raw_response_saved:false};
  fs.writeFileSync('evaluation/results/judge_smoke.json',JSON.stringify(status,null,2));console.log(JSON.stringify(status,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
