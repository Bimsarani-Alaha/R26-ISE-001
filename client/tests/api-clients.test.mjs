import assert from "node:assert/strict";
import { registerHooks } from "node:module";
import { afterEach, test } from "node:test";

// Next.js resolves extensionless TypeScript imports; mirror that in Node tests.
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (
      specifier.startsWith("./") &&
      context.parentURL?.includes("/src/app/lib/")
    ) {
      return nextResolve(`${specifier}.ts`, context);
    }
    return nextResolve(specifier, context);
  },
});

const originalFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = originalFetch;
});

async function expectRequest(moduleName, exportName, input, route, output) {
  const api = await import(`../src/app/lib/${moduleName}.ts`);
  globalThis.fetch = async (url, options) => {
    assert.equal(url, `http://localhost:8000${route}`);
    if (input) {
      assert.equal(options.method, "POST");
      assert.equal(options.headers["Content-Type"], "application/json");
      assert.deepEqual(JSON.parse(options.body), input);
    }
    return Response.json(output);
  };
  assert.deepEqual(await api[exportName](input), output);
}

test("health check reads the fashion backend health endpoint", async () => {
  await expectRequest(
    "aiStyleApi",
    "checkHealth",
    undefined,
    "/fashion-recommendation/api/health",
    { ollama_connected: true, model_name: "qwen2.5:7b" },
  );
});

test("recommendations submit gender, size and requirements to the fashion backend", async () => {
  await expectRequest(
    "aiStyleApi",
    "getRecommendations",
    { gender: "Women", size: "M", requirements: "Blue wedding dress" },
    "/fashion-recommendation/api/recommendations",
    { recommendations: [], total_candidates: 0 },
  );
});

test("stylist requests submit the selected product", async () => {
  await expectRequest(
    "aiStyleApi",
    "getStylistTips",
    { gender: "Women", size: "M", requirements: "Wedding", product_id: "P1" },
    "/fashion-recommendation/api/stylist",
    { summary: "Add silver accessories", accessories: [] },
  );
});

test("health guidance submits measurements to the main backend", async () => {
  await expectRequest(
    "healthTipsApi",
    "fetchHealthTips",
    {
      shoulder_width: 40,
      hip_size: 35,
      height: 170,
      gender: "women",
      clothing_size: "M",
    },
    "/api/health-tips",
    { guidance: "Stay active." },
  );
});

test("system save submits registration data to the main backend", async () => {
  await expectRequest(
    "systemSaveApi",
    "saveSystemData",
    { name: "Test", age: 25 },
    "/api/register",
    { success: true, id: "1" },
  );
});

test("API failures expose the backend detail to the page", async () => {
  const { getRecommendations } = await import("../src/app/lib/aiStyleApi.ts");
  globalThis.fetch = async () =>
    Response.json({ detail: "Invalid size" }, { status: 400 });
  await assert.rejects(
    getRecommendations({ gender: "Women", size: "bad", requirements: "Dress" }),
    /Invalid size/,
  );
});

test("non-JSON errors include the HTTP status", async () => {
  const { checkHealth } = await import("../src/app/lib/aiStyleApi.ts");
  globalThis.fetch = async () => new Response("Bad gateway", { status: 502 });
  await assert.rejects(checkHealth(), /502/);
});

test("network failures identify the unreachable backend and preserve the cause", async () => {
  const { checkHealth } = await import("../src/app/lib/aiStyleApi.ts");
  globalThis.fetch = async () => { throw new TypeError("Failed to fetch"); };
  await assert.rejects(checkHealth(), (error) => {
    assert.match(error.message, /http:\/\/localhost:8000/);
    assert.match(error.message, /Failed to fetch/);
    return true;
  });
});
