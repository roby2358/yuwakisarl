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

test("listLegalMoves rejects higher die for non-furthest checker", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.HUMAN] = 0;
  state.points[5] = { owner: logic.Players.HUMAN, count: 1 };
  state.points[3] = { owner: logic.Players.HUMAN, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.HUMAN, 5);
  const bearMoves = moves.filter(
    (move) => move.kind === "bear" && move.source === 4
  );
  assert.equal(bearMoves.length, 0);
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

test("listLegalMoves rejects higher die for AI non-furthest checker", () => {
  const state = logic.createInitialState();
  state.bar[logic.Players.AI] = 0;
  state.points[0] = { owner: logic.Players.AI, count: 1 };
  state.points[2] = { owner: logic.Players.AI, count: 1 };

  const moves = logic.listLegalMoves(state, logic.Players.AI, 5);
  const bearMoves = moves.filter(
    (move) => move.kind === "bear" && move.source === 3
  );
  assert.equal(bearMoves.length, 0);
});

