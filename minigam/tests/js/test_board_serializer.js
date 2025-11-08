const { strict: assert } = require("node:assert");
const test = require("node:test");

const logic = require("../../resources/public/game_logic.js");
const BoardSerializer = require("../../resources/public/board_serializer.js");

test("serialize returns structured string for populated board", () => {
  const serializer = new BoardSerializer(logic);
  const board = logic.createInitialState();
  board.points[0] = { owner: logic.Players.HUMAN, count: 2 };
  board.points[1] = { owner: logic.Players.AI, count: 1 };
  board.bar[logic.Players.HUMAN] = 3;
  board.bar[logic.Players.AI] = 1;
  board.borneOff[logic.Players.HUMAN] = 4;
  board.borneOff[logic.Players.AI] = 2;

  const result = serializer.serialize(board);
  assert.equal(
    result,
    "points=1:H2,2:A1,3:-,4:-,5:-,6:-;bar=H3,A1;borne=H4,A2",
  );
});

test("serialize returns empty string when board is falsy", () => {
  const serializer = new BoardSerializer(logic);
  const result = serializer.serialize(null);
  assert.equal(result, "");
});

test("serializeState includes dice and player context", () => {
  const serializer = new BoardSerializer(logic);
  const state = {
    board: logic.createInitialState(),
    pendingDice: [3, 1],
    diceRolled: [3, 1],
    turnCompletedDice: [6],
    currentPlayer: logic.Players.HUMAN,
    awaitingRoll: false,
  };

  const result = serializer.serializeState(state);
  assert.ok(
    result.includes("points=") &&
      result.includes("bar=") &&
      result.includes("borne=") &&
      result.includes("pending=3,1") &&
      result.includes("rolled=3,1") &&
      result.includes("completed=6") &&
      result.includes("player=human") &&
      result.includes("awaiting=no"),
  );
});

test("serializeState captures expanded doubles", () => {
  const serializer = new BoardSerializer(logic);
  const state = {
    board: logic.createInitialState(),
    pendingDice: [2, 2, 2, 2],
    diceRolled: [2, 2, 2, 2],
    turnCompletedDice: [],
    currentPlayer: logic.Players.AI,
    awaitingRoll: false,
  };

  const result = serializer.serializeState(state);
  assert.ok(result.includes("pending=2,2,2,2"));
  assert.ok(result.includes("rolled=2,2,2,2"));
});

