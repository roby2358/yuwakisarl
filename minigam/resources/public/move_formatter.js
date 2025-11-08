(function initMoveFormatter(globalObject) {
  "use strict";

  function formatMove(move) {
    if (!move || !move.kind) {
      return null;
    }

    if (move.kind === "enter") {
      return `${move.target}`;
    }

    if (move.kind === "move") {
      return `m ${move.source} ${move.target}`;
    }

    if (move.kind === "bear") {
      return `b ${move.source}`;
    }

    return null;
  }

  function summarizeMoves(moves) {
    if (!Array.isArray(moves) || moves.length === 0) {
      return "no legal moves";
    }

    const seen = new Set();
    const summaries = [];

    for (const move of moves) {
      const summary = formatMove(move);
      if (!summary) {
        continue;
      }
      if (seen.has(summary)) {
        continue;
      }
      summaries.push(summary);
      seen.add(summary);
    }

    if (summaries.length === 0) {
      return "no legal moves";
    }

    return summaries.join("; ");
  }

  const api = {
    formatMove,
    summarizeMoves,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  if (globalObject) {
    globalObject.MinigamMoveFormatter = api;
  }
})(typeof window !== "undefined" ? window : globalThis);


