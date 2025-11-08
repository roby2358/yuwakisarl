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

