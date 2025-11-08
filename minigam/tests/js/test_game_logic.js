const { strict: assert } = require("node:assert");
const test = require("node:test");

const logic = require("../../resources/public/game_logic.js");

test("initial state loads with all checkers on the bar", () => {
  const state = logic.createInitialState();
  assert.equal(state.bar[logic.Players.HUMAN], logic.CHECKERS_PER_PLAYER);
  assert.equal(state.bar[logic.Players.AI], logic.CHECKERS_PER_PLAYER);
  assert.equal(state.points.length, logic.POINT_COUNT);
});

test("entry move handles hits when landing on opposing blot", () => {
  const state = logic.createInitialState();
  const target = 3;
  logic.enterFromBar(state, target, logic.Players.HUMAN);
  assert.equal(state.points[target - 1].owner, logic.Players.HUMAN);
  assert.equal(state.bar[logic.Players.HUMAN], logic.CHECKERS_PER_PLAYER - 1);

  logic.enterFromBar(state, target, logic.Players.AI);
  assert.equal(state.points[target - 1].owner, logic.Players.AI);
  assert.equal(state.bar[logic.Players.HUMAN], logic.CHECKERS_PER_PLAYER);
});

test("listLegalMoves identifies bearing off opportunity", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 1);
  assert.equal(moves.length, 1);
  assert.equal(moves[0].kind, "bear");
});

test("listLegalMoves returns empty when target point is blocked", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[0] = { owner: logic.Players.HUMAN, count: 1 };
  state.points[2] = { owner: logic.Players.AI, count: 2 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 2);
  assert.equal(moves.length, 0);
});

test("bearOff allows checkers on the bar", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 3;
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };

  const dieUsed = logic.bearOff(state, 6, logic.Players.HUMAN);
  assert.equal(dieUsed, 1);
  assert.equal(state.borneOff[logic.Players.HUMAN], 1);
});

test("bearOff allows checkers behind", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };
  state.points[0] = { owner: logic.Players.HUMAN, count: 2 };

  const dieUsed = logic.bearOff(state, 6, logic.Players.HUMAN);
  assert.equal(dieUsed, 1);
  assert.equal(state.borneOff[logic.Players.HUMAN], 1);
  assert.equal(state.points[0].count, 2);
});

test("listLegalMoves includes entry and board moves when bar occupied", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 2;
  state.points[0] = { owner: logic.Players.HUMAN, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 1);
  const kinds = new Set(moves.map((move) => move.kind));
  assert.ok(kinds.has("enter"));
  assert.ok(kinds.has("move"));
});

test("listLegalMoves allows higher die for furthest checker when bar empty", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 3);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  assert.equal(bearMoves.length, 1);
  assert.equal(bearMoves[0].source, 6);
});

test("listLegalMoves forbids higher die bear when exact bear exists", () => {
  const state = logic.createInitialState();
  state.points[0] = { owner: logic.Players.AI, count: 1 };
  state.points[1] = { owner: logic.Players.HUMAN, count: 1 };
  state.points[2] = { owner: logic.Players.AI, count: 1 };
  state.points[3] = { owner: logic.Players.HUMAN, count: 2 };
  state.points[4] = { owner: logic.Players.HUMAN, count: 3 };
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };
  state.bar[logic.Players.HUMAN] = 0;
  state.bar[logic.Players.AI] = 4;
  state.borneOff[logic.Players.HUMAN] = 1;
  state.borneOff[logic.Players.AI] = 2;

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 3);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  const sources = new Set(bearMoves.map((move) => move.source));
  assert.ok(sources.has(4));
  assert.ok(!sources.has(6));
});

test("listLegalMoves provides exact bear when available with higher point occupied", () => {
  const state = logic.createInitialState();
  state.points[0] = { owner: logic.Players.AI, count: 1 };
  state.points[1] = { owner: logic.Players.AI, count: 1 };
  state.points[2] = { owner: null, count: 0 };
  state.points[3] = { owner: logic.Players.HUMAN, count: 4 };
  state.points[4] = { owner: null, count: 0 };
  state.points[5] = { owner: logic.Players.HUMAN, count: 2 };
  state.bar[logic.Players.HUMAN] = 0;
  state.bar[logic.Players.AI] = 2;
  state.borneOff[logic.Players.HUMAN] = 2;
  state.borneOff[logic.Players.AI] = 4;

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 3);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  assert.ok(bearMoves.some((move) => move.source === 4));
});

test("listLegalMoves uses higher die on human lowest point when no exact bear", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[4] = { owner: logic.Players.HUMAN, count: 2 };
  state.points[5] = { owner: logic.Players.HUMAN, count: 3 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 6);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  const sources = new Set(bearMoves.map((move) => move.source));
  assert.ok(sources.has(5));
  assert.ok(!sources.has(6));
});

test("listLegalMoves rejects higher die for human checker closer to exit", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };
  state.points[3] = { owner: logic.Players.HUMAN, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 5);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  const sources = new Set(bearMoves.map((move) => move.source));
  assert.ok(sources.has(4));
  assert.ok(!sources.has(6));
});

test("listLegalMoves allows higher die for AI furthest checker when bar empty", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.AI] = 0;
  state.points[0] = { owner: logic.Players.AI, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.AI, 3);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  assert.equal(bearMoves.length, 1);
  assert.equal(bearMoves[0].source, 1);
});

test("listLegalMoves uses higher die on AI highest point when no exact bear", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.AI] = 0;
  state.points[0] = { owner: logic.Players.AI, count: 1 };
  state.points[2] = { owner: logic.Players.AI, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.AI, 5);
  const bearMoves = moves.filter((move) => move.kind === "bear");
  const sources = new Set(bearMoves.map((move) => move.source));
  assert.ok(sources.has(3));
  assert.ok(!sources.has(1));
});

