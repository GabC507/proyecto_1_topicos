(function (root, factory) {
  const createRequestSequence = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = createRequestSequence;
  } else {
    root.createRequestSequence = createRequestSequence;
  }
})(globalThis, function () {
  return function createRequestSequence() {
    let latest = 0;
    return {
      next() {
        latest += 1;
        return latest;
      },
      invalidate() {
        latest += 1;
      },
      isCurrent(requestId) {
        return requestId === latest;
      },
    };
  };
});
