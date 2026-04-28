# DealsPlatform

AI-curated deal channels for India, built on top of the existing
`stock_notifier` engine. Designed from first principles around four ideas:

1. **Hexagonal architecture.** Business logic depends on ports
   (`deals_platform/domain/ports.py`); adapters live in `storage/`, `llm/`,
   `notify/`, `sources/`. Swap any adapter without touching the pipeline.
2. **Event-driven pipeline.** Every stage is a coroutine that consumes one
   event type from the bus and produces another. Today the bus is in-memory;
   moving to Redis Streams or NATS is one class change.
3. **Verified, not vibes.** Every deal is scored against your own price
   history (90-day min, 30-day median, cross-retailer min). The LLM never
   sees a "discount %" without the underlying numbers.
4. **Configuration is platform.** Adding a category, retailer, source, or
   notifier is a YAML edit, not a code change.

## Run it

```bash
cp .env.example .env   # fill in DATABASE_URL, LLM_API_KEY, notifier creds
pip install -r requirements.txt
python -m deals_platform
```

Or with Docker:

```bash
docker compose up -d deals-platform
```

The legacy stock notifier is unchanged and can run side-by-side:

```bash
docker compose --profile legacy up -d stock-notifier
# or
python -m stock_notifier
```

## Layers

```
sources/        ingest events from retailers + aggregators
domain/         pure types and business contracts (ports)
pipeline/       normalize -> score -> curate
llm/            pluggable LLM (Gemini OpenAI-compat by default)
storage/        Postgres adapters for ports
notify/         per-platform notifier adapters + ChannelRouter
bus/            in-memory pub/sub
runtime/        composition root + entrypoint
config/platform/   channels.yaml, sources.yaml, scoring.yaml
```

## How a deal flows

```
WatchSpec / Aggregator post
   ↓ Source.stream()
DealCandidate (raw)
   ↓ Normalizer (canonical id, append history, fetch min/median/cross)
EnrichedDeal
   ↓ CompositeScorer (transparent multi-signal)
ScoredDeal (only if ≥ threshold)
   ↓ CuratorAgent (LLM: publish? category? copy?)
PublishablePost
   ↓ ChannelRouter
Telegram + Discord + WhatsApp + Twitter + Email
```

## Adding things

**A new category** → append to `config/platform/channels.yaml`. The curator
already routes by `Category` enum value; if you add a new enum value, edit
`deals_platform/domain/models.py` once.

**A new retailer** → write a small extractor function in
`deals_platform/sources/retailers/price_extract.py` and register it in
`_EXTRACTORS`. Add watches in `config/platform/sources.yaml`.

**A new notifier** → add a class with `name: str` and
`async def send(post, channel_target)` in `deals_platform/notify/`,
register it in `runtime/app.py`, reference it in `channels.yaml` bindings.

**A new LLM provider** → implement the `LLMClient` port. Default already
works for Gemini, OpenAI, OpenRouter, Together, Groq, local llama.cpp.

**A new source (aggregator)** → implement `Source` (just a
`stream()` async iterator yielding `DealCandidate`). Register in
`sources.yaml` + wire in `runtime/app.py`.

## Scaling roadmap

- **v1 (today):** single process, in-memory bus, Postgres for history & dedupe.
- **v2:** swap `InMemoryBus` for `RedisStreamBus`. Each stage becomes its own
  worker process; sources run on cheap boxes, LLM workers on better ones.
- **v3:** SaaSify — every user gets their own watchlist & channel bindings;
  multi-tenant tables already keyed by `canonical_id` so adding a `tenant_id`
  is mechanical.
