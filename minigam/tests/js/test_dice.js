const { strict: assert } = require("node:assert");
const test = require("node:test");

const Dice = require("../../resources/public/dice.js");

function generator(values) {
  let index = 0;
  return () => {
    if (index >= values.length) {
      return values[values.length - 1];
    }
    const value = values[index];
    index += 1;
    return value;
  };
}

test("roll produces pending and rolled dice", () => {
  const dice = new Dice(generator([3, 5]));

  const roll = dice.roll();

  assert.deepEqual(roll, [3, 5]);
  assert.deepEqual(dice.pending, [3, 5]);
  assert.deepEqual(dice.rolled, [3, 5]);
  assert.equal(dice.awaitingRoll, false);
});

test("roll expands doubles into four dice", () => {
  const dice = new Dice(generator([2, 2]));

  const roll = dice.roll();

  assert.deepEqual(roll, [2, 2, 2, 2]);
  assert.deepEqual(dice.pending, [2, 2, 2, 2]);
  assert.equal(dice.completed.length, 0);
});

test("consume removes die and returnValue restores it", () => {
  const dice = new Dice(generator([4, 6]));
  dice.roll();

  const consumption = dice.consume(4);

  assert.ok(consumption);
  assert.deepEqual(dice.pending, [6]);
  assert.deepEqual(dice.completed, [4]);

  dice.returnValue(consumption);

  assert.deepEqual(dice.pending, [4, 6]);
  assert.deepEqual(dice.completed, []);
});

test("snapshot and restore rebuild dice state", () => {
  const dice = new Dice(generator([5, 5]));
  dice.roll();
  const firstTake = dice.consume(5);
  const snapshot = dice.snapshot();

  dice.consume(5);
  dice.reset();
  dice.restore(snapshot);

  assert.deepEqual(dice.pending, [5, 5, 5]);
  assert.deepEqual(dice.rolled, [5, 5, 5, 5]);
  assert.deepEqual(dice.completed, [5]);
  dice.returnValue(firstTake);
  assert.deepEqual(dice.pending, [5, 5, 5, 5]);
});

test("roll throws when generator yields invalid value", () => {
  const dice = new Dice(generator([0, 4]));
  assert.throws(() => dice.roll(), /Invalid die value/);
});


