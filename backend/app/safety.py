"""Single-process public-demo limits; no IP tracking or forwarded-header trust."""
import json
import time
from collections import deque


class RequestSafety:
    def __init__(self, app, plan_per_minute=60, interpret_per_minute=10, interpret_per_day=200, max_bytes=32768, clock=time.monotonic):
        self.app, self.max_bytes, self.clock = app, max_bytes, clock
        self.limits = {'/api/plan': [(60, plan_per_minute, deque())],
                       '/api/interpret': [(60, interpret_per_minute, deque()), (86400, interpret_per_day, deque())]}

    async def reject(self, send, status, message, retry=None):
        headers=[(b'content-type', b'application/json'), (b'cache-control', b'no-store')]
        if retry is not None: headers.append((b'retry-after', str(retry).encode()))
        await send({'type':'http.response.start','status':status,'headers':headers})
        await send({'type':'http.response.body','body':json.dumps({'detail':message}).encode()})

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or scope['path'] not in self.limits:
            return await self.app(scope, receive, send)
        chunks=[]; size=0
        while True:
            event=await receive()
            if event['type']=='http.disconnect': return
            chunk=event.get('body',b''); size+=len(chunk)
            if size>self.max_bytes:
                return await self.reject(send,413,'Request is too large. Use shorter planning inputs.')
            chunks.append(chunk)
            if not event.get('more_body',False): break
        now=self.clock(); windows=self.limits[scope['path']]
        for seconds,limit,entries in windows:
            while entries and entries[0]<=now-seconds: entries.popleft()
            if len(entries)>=limit:
                return await self.reject(send,429,'Demo request limit reached. Retry later; structured controls do not require OpenAI.',max(1,int(seconds-(now-entries[0]))+1))
        for _,_,entries in windows: entries.append(now)
        consumed=False
        async def buffered_receive():
            nonlocal consumed
            if not consumed:
                consumed=True
                return {'type':'http.request','body':b''.join(chunks),'more_body':False}
            return await receive()
        await self.app(scope, buffered_receive, send)
