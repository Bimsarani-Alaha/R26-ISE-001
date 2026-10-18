const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const ts = require("typescript");

const source = fs.readFileSync(
  path.join(__dirname, "../src/app/lib/recommendationGroups.ts"),
  "utf8",
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;
const moduleExports = {};
new Function("exports", compiled)(moduleExports);
const { buildRecommendationGroups } = moduleExports;

const exact = {
  product_id: "exact",
  match_category: "exact",
  occasion: "Formal",
};
const alternative = {
  product_id: "alternative",
  match_category: "alternative",
  occasion: "Formal",
  unmatched_requirements: ["colour"],
};

test("shows alternatives when there are no exact matches", () => {
  assert.deepEqual(buildRecommendationGroups([alternative], ["Formal"]), [
    { title: "Similar Alternatives", items: [alternative] },
  ]);
});

test("keeps alternatives separate after exact matches", () => {
  assert.deepEqual(
    buildRecommendationGroups([alternative, exact], ["Formal"]),
    [
      { title: "Primary Recommendations", items: [exact] },
      { title: "Similar Alternatives", items: [alternative] },
    ],
  );
});

test("preserves occasion groups and appends alternatives without an occasion request", () => {
  assert.deepEqual(buildRecommendationGroups([alternative, exact], null), [
    { title: "Formal", items: [exact] },
    { title: "Similar Alternatives", items: [alternative] },
  ]);
  assert.deepEqual(buildRecommendationGroups([], null), []);
});
