import { Seed } from '../lib/types';
export function TasteDNA({seeds,interests}:{seeds:Seed[];interests:string[]}) {
  const dimensions=[['Music',seeds.filter(s=>s.category==='artist').length],['Film',seeds.filter(s=>s.category==='movie').length],['Books',seeds.filter(s=>s.category==='book').length],['Brands',seeds.filter(s=>s.category==='brand').length],['Interests',interests.length]] as const;
  return <section className="dna"><div className="eyebrow">Your taste, at a glance</div><h3>An original mix.<br/>{' '}Entirely yours.</h3><p>The ingredients of your day, drawn from what you’ve shared.</p><div className="dna-bars">{dimensions.map(([name,n])=><div key={name}><span>{name}</span><div className="track"><i style={{width:`${Math.min(n/6,1)*100}%`}}/></div><b>{n}</b></div>)}</div><p className="dna-note">Taste DNA counts your own inputs. No inferred personality scores.</p></section>;
}
