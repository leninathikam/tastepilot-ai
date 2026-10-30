"""Opt-in bounded live smoke test. Does not save raw Qloo responses or credentials."""
import argparse
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from backend.app.models import Seed
from backend.app.qloo import QlooClient, IntegrationError

ROOT=Path(__file__).resolve().parents[1]


async def probe(execute=False):
    load_dotenv(ROOT/'.env')
    key=os.getenv('QLOO_API_KEY','')
    status={'checked_at':datetime.now(timezone.utc).isoformat(),'live_verified':False,'calls':None,
            'search_verified':False,'insights_verified':False,'same_pool_rescore_verified':False}
    if not key or key.startswith('replace_'):
        status['blocker']='QLOO_API_KEY missing or placeholder; no API request sent'
    elif not execute:
        status['blocker']='Credential present. Run with --execute to permit the bounded live probe.'
    else:
        client=None
        try:
            client=QlooClient(key,os.getenv('QLOO_API_URL','https://hackathon.api.qloo.com'))
            async with asyncio.timeout(60):
                identifier=await client.resolve(Seed(name='Radiohead'))
                if not identifier:raise IntegrationError('Exact Radiohead resolution returned no unambiguous match')
                status['search_verified']=True
                candidates=await client.discover([identifier],'Chicago')
                if not candidates:raise IntegrationError('No Chicago places returned')
                status['insights_verified']=True
                rescored=await client.discover([identifier],'Chicago',entity_ids=[c.id for c in candidates[:5]])
                if not rescored or not {c.id for c in rescored}.issubset({c.id for c in candidates[:5]}):
                    raise IntegrationError('Same-pool rescore could not be validated')
                status['same_pool_rescore_verified']=True
                status['live_verified']=True
                status['candidate_count']=len(candidates)
                status['note']='Transport, parsing and scoped IDs verified only; venue facts and recommendation quality unverified.'
        except IntegrationError as exc:
            status['blocker']=str(exc)
        except Exception:
            status['blocker']='Live probe failed; inspect local connectivity/configuration without exposing credentials'
        finally:
            status['calls']=client.calls if client else 0
    (ROOT/'evaluation/results/live_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print(json.dumps(status,indent=2))
    return status

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true')
    asyncio.run(probe(parser.parse_args().execute))
