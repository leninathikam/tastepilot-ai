# Risk register

| Risk | Mitigation / current status |
|---|---|
| Missing credentials | Ignored .env placeholders; explicit fixture mode; live integration unverified |
| Event quota/expiry unspecified | Bounded calls/retries; confirm with organizer before public load |
| Unknown practical facts | Separate provisional candidates; fail closed for hard requirements |
| Ambiguous entity names | Exact unique match; surface unresolved inputs |
| Taste overclaim | Ordinal ranking is relative, not personal satisfaction or causality |
| Public endpoint abuse | Concurrency bound; deployment must add edge rate limiting |
| External text injection | No executable tools from retrieved content; validated models |
| Deadline | Single deployable backend and frontend; no stretch group feature |
| Publishing | Requires user authorization; no public push or deployment yet |
| Qloo data rights | No durable live response corpus; confirm license before release |
