const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const ts = require("typescript");

const sourcePath = path.join(
  __dirname,
  "../src/app/lib/recommendationPrefill.ts",
);
const source = fs.readFileSync(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;
const moduleExports = {};
new Function("exports", compiled)(moduleExports);
const { getRecommendationPrefill } = moduleExports;

test("preselects saved pose gender and predicted size ahead of an older recommendation size", () => {
  assert.deepEqual(
    getRecommendationPrefill({
      gender: "Women",
      predictedSize: "L",
      size: "S",
    }),
    {
      gender: "Female",
      size: "L",
      predictedGender: "Female",
      predictedSize: "L",
    },
  );
});

test("normalizes engine size aliases and gender values to available choices", () => {
  for (const [gender, predictedSize, expectedGender, expectedSize] of [
    [" men ", " xxl ", "Male", "2XL"],
    ["FEMALE", "xxxl", "Female", "3XL"],
    ["Unisex", "4xl", "Unisex", "4XL"],
  ]) {
    const result = getRecommendationPrefill({ gender, predictedSize });
    assert.equal(result.gender, expectedGender);
    assert.equal(result.size, expectedSize);
  }
});

test("retains measurement fallback for the existing size page flow", () => {
  assert.deepEqual(
    getRecommendationPrefill({
      bodyMeasurements: { gender: "Men", clothingSize: "M" },
    }),
    {
      gender: "Male",
      size: "M",
      predictedGender: "Male",
      predictedSize: "M",
    },
  );
});

test("uses saved recommendation size when no usable prediction exists", () => {
  assert.deepEqual(
    getRecommendationPrefill({
      gender: "Female",
      predictedSize: "invalid",
      size: "XS",
    }),
    {
      gender: "Female",
      size: "XS",
      predictedGender: "",
      predictedSize: "",
    },
  );
});

test("ignores missing or malformed storage values", () => {
  for (const values of [
    {},
    { gender: 123, predictedSize: {}, size: null },
    { gender: "unknown", predictedSize: "5XL" },
  ]) {
    assert.deepEqual(getRecommendationPrefill(values), {
      gender: "",
      size: "",
      predictedGender: "",
      predictedSize: "",
    });
  }
});
