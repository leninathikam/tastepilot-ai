import Image, { StaticImageData } from 'next/image';
import { ArrowUpRight, ChevronDown, RefreshCw } from 'lucide-react';
import { Candidate } from '../lib/types';
import food from '../public/images/korean-table.jpg';
import records from '../public/images/records.jpg';
import gallery from '../public/images/gallery.jpg';
import restaurant from '../public/images/restaurant.jpg';

// Only explicitly authored fictional examples receive contextual photography.
// Live entities never inherit stock photos that could misrepresent their venue.
const examples:Record<string,{image:StaticImageData;alt:string;description:string}>={
  'fixture:0':{image:food,alt:'Korean bibimbap, shown as food inspiration only',description:'A Korean-food stop to build your day around.'},
  'fixture:1':{image:records,alt:'Vinyl records, shown as music inspiration only',description:'Make a little time for your love of indie music.'},
  'fixture:2':{image:gallery,alt:'Gallery visitors, shown as art inspiration only',description:'A pause for contemporary art and a fresh perspective.'},
  'fixture:3':{image:restaurant,alt:'Restaurant interior, shown as dining inspiration only',description:'An alternative dining stop for the Chicago example.'},
  'fixture:5':{image:records,alt:'Vinyl browsing, shown as music inspiration only',description:'Keep your music interests in the mix, on a smaller budget.'},
};

export function ExperienceCard({candidate:c,index,alternative,busy,onReplace}:{candidate:Candidate;index:number;alternative:boolean;busy:boolean;onReplace:()=>void}) {
  const editorial=c.source==='fixture'?examples[c.id]:undefined;
  return <article className={`stop ${editorial?'with-photo':'text-only'}`}>
    {editorial&&<figure className="stop-photo"><div><Image src={editorial.image} alt={editorial.alt} fill sizes="(max-width: 680px) 100vw, 280px" placeholder="blur"/></div><figcaption>Inspiration photo · not this venue</figcaption></figure>}
    <div className="stop-content"><div className="card-meta"><span>{alternative?'Another possibility':`Stop ${String(index+1).padStart(2,'0')}`} <span aria-hidden="true">/</span> {c.category==='place'?'Place discovery':c.category}</span><span>{c.source==='fixture'?'Fictional example':'From Qloo'}</span></div>
      <h3>{c.name}</h3>
      {editorial&&<p className="editorial-description">{editorial.description}</p>}
      <div className="tags" aria-label="Related interests">{c.tags.map(t=><span key={t}>{t}</span>)}</div>
      <details className="recommendation-evidence"><summary>Why it’s in your day <ChevronDown size={14}/></summary><p>{c.explanation}</p><p>{c.warnings.join('. ')}</p><dl><div><dt>Entity</dt><dd>{c.id}</dd></div><div><dt>Taste order</dt><dd>#{c.taste_rank}</dd></div><div><dt>Relative taste signal</dt><dd>{c.taste_score.toFixed(2)}</dd></div><div><dt>Weighted ranking</dt><dd>{c.score.toFixed(2)}</dd></div></dl>{c.address&&<p>Qloo-provided address: {c.address}</p>}{c.source_url&&<a href={c.source_url} target="_blank" rel="noopener noreferrer">Visit source <ArrowUpRight size={14}/></a>}</details>
      {!!c.member_evidence?.length&&<details className="member-evidence"><summary>Whose taste does this connect with?</summary>{c.member_evidence.map(e=><p key={e.label}><b>{e.label}</b> · {e.returned_rank===null?'No returned taste evidence':`#${e.returned_rank} in their ${e.source==='fixture'?'synthetic':'Qloo'} ordering`} · modeled proxy {e.proxy.toFixed(2)}. {e.note}</p>)}</details>}
      <div className="stop-end"><div><strong>{c.cost===null?'Price unverified':`$${c.cost}`}</strong><small>{c.cost===null?'Confirm before you go':' / person · simulated'}</small></div>{(!alternative||c.source==='qloo')&&<button disabled={busy} onClick={onReplace} aria-label={`Replace ${c.name}`}><RefreshCw size={14}/> Try something else</button>}</div>
    </div>
  </article>;
}
