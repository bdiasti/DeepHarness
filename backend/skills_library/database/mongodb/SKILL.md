---
name: mongodb
description: MongoDB — document modeling, aggregation pipelines, indexing, replica sets
---

# MongoDB

Document database. Choose it when data is naturally hierarchical, schemas evolve, or you need horizontal scale via sharding.

## Document Modeling

Rule of thumb: **data that's read together should live together**. Embed vs reference:

- **Embed** when child is bounded, not queried independently, and updated with parent (e.g., order line items inside order).
- **Reference** when child is large, unbounded (comments on viral post), or shared across parents (users referenced by orders).

```js
// good: order with embedded items (bounded, atomic updates)
{
  _id: ObjectId(),
  userId: ObjectId("..."),
  status: "paid",
  total: 89.90,
  items: [
    { sku: "A1", name: "Shirt", qty: 2, price: 29.95 },
    { sku: "B2", name: "Hat",   qty: 1, price: 29.95 },
  ],
  createdAt: ISODate(),
}
```

Avoid unbounded arrays (>~1000 elements) in a single doc (16MB limit, slow updates). Use the **bucket pattern** for time-series or **outlier pattern** when most docs are small but a few huge.

## Indexes

```js
db.orders.createIndex({ userId: 1, createdAt: -1 });
db.users.createIndex({ email: 1 }, { unique: true });
db.products.createIndex({ name: "text", description: "text" });
db.events.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 });  // TTL
db.places.createIndex({ location: "2dsphere" });                      // geo
db.orders.createIndex({ status: 1 }, { partialFilterExpression: { status: "open" } });
```

ESR rule for compound indexes: **Equality, Sort, Range** (in that order).
Use `.explain("executionStats")` — want `IXSCAN`, not `COLLSCAN`; `totalKeysExamined` close to `nReturned`.

## Aggregation Pipeline

```js
db.orders.aggregate([
  { $match: { status: "paid", createdAt: { $gte: ISODate("2026-01-01") } } },
  { $unwind: "$items" },
  { $group: {
      _id: "$items.sku",
      revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } },
      units:   { $sum: "$items.qty" },
  }},
  { $sort: { revenue: -1 } },
  { $limit: 10 },
  { $lookup: { from: "products", localField: "_id", foreignField: "sku", as: "product" } },
  { $set: { product: { $first: "$product" } } },
]);
```

Tips: `$match` and `$project` early to shrink docs; ensure `$match` hits an index; `$lookup` is a join — use sparingly and index the foreign field.

## CRUD Patterns

```js
// upsert
db.users.updateOne({ email }, { $set: { name }, $setOnInsert: { createdAt: new Date() } }, { upsert: true });

// atomic increments and array ops
db.inventory.updateOne({ sku: "A1", qty: { $gte: 1 } }, { $inc: { qty: -1 } });
db.posts.updateOne({ _id }, { $push: { tags: { $each: ["new"], $slice: -20 } } });

// multi-doc transaction (replica set required)
const s = client.startSession();
await s.withTransaction(async () => {
  await orders.insertOne({ ... }, { session: s });
  await inventory.updateOne({ sku }, { $inc: { qty: -1 } }, { session: s });
});
```

Prefer single-document atomic ops over transactions when possible — they're much faster.

## Replica Sets & Sharding

- **Replica set**: 3+ nodes; primary handles writes, secondaries replicate. Use read preference `primary` (default) for consistency, `secondaryPreferred` only for analytics where staleness is OK.
- **Write concern** `w: "majority"` for durability; `j: true` waits for journal.
- **Read concern** `majority` to avoid reading rolled-back data.
- **Sharding** distributes by shard key — pick one with high cardinality, low frequency, and monotonic avoidance (hashed `_id` or compound). Wrong shard key is painful to fix.

## Operations

- Schema validation with `$jsonSchema` on collections for contracts
- Monitor via Atlas or `mongostat`/`mongotop`; watch working set vs RAM
- Use **Atlas** or Ops Manager for managed backups and point-in-time restore
- Connection pooling via official driver; tune `maxPoolSize`
- Always set `readConcern`/`writeConcern` explicitly for critical paths
