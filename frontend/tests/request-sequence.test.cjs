const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const test = require("node:test");

const createRequestSequence = require("../request-sequence.js");
const html = readFileSync(join(__dirname, "..", "index.html"), "utf8");

function delayed() {
  let resolve;
  const promise = new Promise((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

test("service and month changes invalidate pending slot requests", () => {
  const selectService = html.match(/function selectService\(s, el\)\{([\s\S]*?)\n  \}/);
  const changeMonth = html.match(/function changeMonth\(delta\)\{([\s\S]*?)\n  \}/);
  assert.ok(selectService);
  assert.ok(changeMonth);
  assert.match(selectService[1], /slotsRequests\.invalidate\(\)/);
  assert.match(changeMonth[1], /slotsRequests\.invalidate\(\)/);
  assert.match(html, /if\(!slotsRequests\.isCurrent\(myReq\)\) return/);
});

test("a delayed response from an old date cannot replace newer slots", async () => {
  const sequence = createRequestSequence();
  let renderedSlots = [];
  const oldResponse = delayed();

  async function renderWhenCurrent(response) {
    const requestId = sequence.next();
    const slots = await response;
    if (!sequence.isCurrent(requestId)) return;
    renderedSlots = slots;
  }

  const oldRequest = renderWhenCurrent(oldResponse.promise);
  sequence.invalidate(); // Same invalidation used when month/service changes.
  await renderWhenCurrent(Promise.resolve(["12:30"]));
  oldResponse.resolve(["10:00"]);
  await oldRequest;

  assert.deepEqual(renderedSlots, ["12:30"]);
});
