import Image from 'next/image';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import food from '../public/images/korean-table.jpg';
import restaurant from '../public/images/restaurant.jpg';
import records from '../public/images/records.jpg';
import gallery from '../public/images/gallery.jpg';

export function EditorialIntro() {
  return <>
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-copy">
        <p className="eyebrow">For the joy of discovering</p>
        <h1 id="hero-title">Good food.<br/>Great company.<br/><em>Your kind of day.</em></h1>
        <p className="hero-description">A long lunch. A record you’ve never heard. A little gallery you almost walked past. Find the places that bring your tastes together.</p>
        <a className="primary hero-action" href="#workspace">Plan a day out <ArrowRight size={18}/></a>
        <p className="hero-note">Made personal with cultural insights from Qloo.</p>
      </div>
      <figure className="hero-photo">
        <div className="photo-frame"><Image src={food} alt="A Korean bibimbap bowl with vegetables and egg, served with soup at a sunlit table" fill sizes="(max-width: 760px) 100vw, 55vw" priority placeholder="blur"/></div>
        <figcaption><span><b>Start with something you love.</b><br/>Let curiosity take care of the rest.</span><span className="photo-credit">Food inspiration<br/>Photo by Change C.C / Pexels</span></figcaption>
      </figure>
    </section>
    <section className="editorial" aria-labelledby="editorial-title">
      <div className="editorial-heading"><div><p className="eyebrow">Follow your curiosity</p><h2 id="editorial-title">There’s more than one way to spend a day.</h2></div><a href="#taste-profile">Start with your taste <ArrowUpRight size={16}/></a></div>
      <div className="story-grid">
        {[{image:restaurant,alt:'Warm wooden tables and woven chairs in a light-filled restaurant',label:'Around the table',title:'Make room for a long lunch.',copy:'Food, conversation, and somewhere worth lingering.'},
          {image:records,alt:'Vinyl albums waiting to be browsed in a record shop',label:'Off the beaten track',title:'Find your next favorite sound.',copy:'Let the music you love lead you somewhere new.'},
          {image:gallery,alt:'Visitors quietly viewing a painting through an arched gallery doorway',label:'A different perspective',title:'Leave a little space for art.',copy:'For the moments that make you stop and look.'}].map(story=><a className="story" href="#taste-profile" key={story.label}><div className="story-photo"><Image src={story.image} alt={story.alt} fill placeholder="blur" sizes="(max-width: 600px) 88vw, 33vw"/></div><div className="story-label">{story.label}<ArrowUpRight size={15}/></div><h3>{story.title}</h3><p>{story.copy}</p></a>)}
      </div>
      <p className="imagery-note">A little inspiration for your day — photography shows cultural themes, not recommended venues.</p>
    </section>
    <section className="how-strip" id="how" aria-label="How TastePilot works"><p>Personal taste.<br/><em>Thoughtful plans.</em></p><div><span>01</span><b>Tell us what you love</b><small>Music, films, food, and everything in between.</small></div><div><span>02</span><b>Find the connections</b><small>Explore places through cultural affinities.</small></div><div><span>03</span><b>Make it your own</b><small>Check the details. Change your mind. Go explore.</small></div></section>
  </>;
}
