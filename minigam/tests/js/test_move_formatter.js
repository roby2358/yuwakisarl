const { strict: assert } = require("node:assert");
const test = require("node:test");

const formatter = require("../../resources/public/move_formatter.js");

test("summarizeMoves returns no legal moves when list empty", () => {
  assert.equal(formatter.summarizeMoves([]), "no legal moves");
});

test("formatMove maps to terse command syntax", () => {
  const move = { kind: "move", source: 2, target: 4, die: 2 };
  assert.equal(formatter.formatMove(move), "m 2 4");
});

test("summarizeMoves deduplicates identical move descriptions", () => {
  const moves = [
    { kind: "enter", source: "bar", target: 3, die: 3 },
    { kind: "enter", source: "bar", target: 3, die: 3 },
    { kind: "bear", source: 6, target: "off", die: 1 },
  ];

  const summary = formatter.summarizeMoves(moves);
  assert.equal(summary, "3; b 6");
});


