import assert from "node:assert/strict";
import { test } from "node:test";
import { buildRecommendationGroups } from "../src/app/lib/recommendationGroups.ts";

const product = (id, occasion, category = "exact") => ({
  product_id: id, occasion, match_category: category,
});

test("missing occasion groups primary results by nonempty catalogue categories", () => {
  const groups = buildRecommendationGroups([
    product("1", "Wedding"), product("2", "Party / Casual"), product("3", "Formal"),
  ], null);
  assert.deepEqual(groups.map(g => g.title), ["Wedding", "Party", "Casual", "Formal"]);
  assert.deepEqual(groups.map(g => g.items.map(p => p.product_id)), [["1"], ["2"], ["2"], ["3"]]);
});

test("provided occasion displays only primary recommendations", () => {
  const groups = buildRecommendationGroups([
    product("1", "Wedding"), product("2", "Wedding", "alternative"),
  ], ["Wedding"]);
  assert.deepEqual(groups.map(g => g.title), ["Primary Recommendations"]);
  assert.deepEqual(groups[0].items.map(p => p.product_id), ["1"]);
});

test("alternatives are excluded when grouping by occasion", () => {
  const groups = buildRecommendationGroups([
    product("1", "Wedding"), product("2", "Party", "alternative"),
  ], null);
  assert.deepEqual(groups.map(g => g.title), ["Wedding"]);
});

test("alternative-only results produce no display groups", () => {
  const items = [product("1", "Wedding", "alternative")];
  assert.deepEqual(buildRecommendationGroups(items, null), []);
  assert.deepEqual(buildRecommendationGroups(items, ["Wedding"]), []);
});

test("unknown occasions are not silently assigned or discarded and duplicates are removed", () => {
  const groups = buildRecommendationGroups([
    product("1", null), product("2", "wedding, Wedding"),
  ], null);
  assert.deepEqual(groups.map(g => g.title), ["Wedding", "Occasion unspecified"]);
  assert.equal(groups[0].items.length, 1);
  assert.deepEqual(buildRecommendationGroups([], null), []);
});

test("N/A occasion is treated as missing rather than split into categories", () => {
  const groups = buildRecommendationGroups([product("1", "N/A")], null);
  assert.deepEqual(groups.map(g => g.title), ["Occasion unspecified"]);
});
