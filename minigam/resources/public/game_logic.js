/* eslint-disable no-param-reassign */
const Players = Object.freeze({
  HUMAN: "human",
  AI: "ai",
});

const CHECKERS_PER_PLAYER = 8;
const POINT_COUNT = 6;

const opposite = (player) =>
  player === Players.HUMAN ? Players.AI : Players.HUMAN;

const clonePoints = (points) =>
  points.map((point) => ({ owner: point.owner, count: point.count }));

function closestToExitPoint(state, player) {
  if (player === Players.HUMAN) {
    for (let point = POINT_COUNT; point >= 1; point -= 1) {
      const entry = state.points[point - 1];
      if (entry.owner === player && entry.count > 0) {
        return point;
      }
    }
    return null;
  }

  for (let point = 1; point <= POINT_COUNT; point += 1) {
    const entry = state.points[point - 1];
    if (entry.owner === player && entry.count > 0) {
      return point;
    }
  }
  return null;
}

function createInitialState() {
  return {
    points: Array.from({ length: POINT_COUNT }, () => ({
      owner: null,
      count: 0,
    })),
    bar: {
      [Players.HUMAN]: CHECKERS_PER_PLAYER,
      [Players.AI]: CHECKERS_PER_PLAYER,
    },
    borneOff: {
      [Players.HUMAN]: 0,
      [Players.AI]: 0,
    },
  };
}

const withinBoard = (pointNumber) =>
  pointNumber >= 1 && pointNumber <= POINT_COUNT;

function isPointOpen(state, player, targetPoint) {
  if (!withinBoard(targetPoint)) {
    return false;
  }

  const point = state.points[targetPoint - 1];
  if (!point.owner || point.owner === player) {
    return true;
  }

  return point.count === 1;
}

function resolveEntryTarget(player, die) {
  if (player === Players.HUMAN) {
    return die;
  }

  return POINT_COUNT + 1 - die;
}

function entryDieForTarget(player, targetPoint) {
  if (player === Players.HUMAN) {
    return targetPoint;
  }

  return POINT_COUNT + 1 - targetPoint;
}

function computeTarget(player, originPoint, die) {
  if (player === Players.HUMAN) {
    return originPoint + die;
  }

  return originPoint - die;
}

function computeOrigin(candidateTarget, die, player) {
  if (player === Players.HUMAN) {
    return candidateTarget - die;
  }

  return candidateTarget + die;
}

function bearingDie(pointNumber, player) {
  if (player === Players.HUMAN) {
    return POINT_COUNT + 1 - pointNumber;
  }

  return pointNumber;
}

function hasCheckersBehind(state, pointNumber, player) {
  if (player === Players.HUMAN) {
    return state.points
      .slice(0, pointNumber - 1)
      .some((p) => p.owner === player && p.count > 0);
  }

  return state.points
    .slice(pointNumber)
    .some((p) => p.owner === player && p.count > 0);
}

function applyHit(state, targetPoint, player) {
  const point = state.points[targetPoint - 1];
  if (point.owner !== player && point.count === 1) {
    state.bar[point.owner] += 1;
    point.owner = null;
    point.count = 0;
  }
}

function incrementPoint(state, pointNumber, player) {
  const point = state.points[pointNumber - 1];
  if (point.owner && point.owner !== player) {
    throw new Error("Cannot increment point owned by opponent");
  }

  point.owner = player;
  point.count += 1;
}

function decrementPoint(state, pointNumber) {
  const point = state.points[pointNumber - 1];
  if (point.count <= 0) {
    throw new Error("Cannot decrement empty point");
  }

  point.count -= 1;
  if (point.count === 0) {
    point.owner = null;
  }
}

function enterFromBar(state, targetPoint, player) {
  const dieRequired = entryDieForTarget(player, targetPoint);
  if (state.bar[player] <= 0) {
    throw new Error("No checker on the bar");
  }

  if (!isPointOpen(state, player, targetPoint)) {
    throw new Error("Target point blocked");
  }

  state.bar[player] -= 1;
  applyHit(state, targetPoint, player);
  incrementPoint(state, targetPoint, player);
  return dieRequired;
}

function moveChecker(state, originPoint, targetPoint, player) {
  if (!withinBoard(originPoint)) {
    throw new Error("Origin out of range");
  }

  const origin = state.points[originPoint - 1];
  if (origin.owner !== player || origin.count === 0) {
    throw new Error("No checker owned by player on origin");
  }

  if (!withinBoard(targetPoint)) {
    throw new Error("Target out of range");
  }

  if (!isPointOpen(state, player, targetPoint)) {
    throw new Error("Target point blocked");
  }

  decrementPoint(state, originPoint);
  applyHit(state, targetPoint, player);
  incrementPoint(state, targetPoint, player);
  return Math.abs(targetPoint - originPoint);
}

function bearOff(state, pointNumber, player) {
  const point = state.points[pointNumber - 1];
  if (point.owner !== player || point.count === 0) {
    throw new Error("No checker to bear off");
  }

  decrementPoint(state, pointNumber);
  state.borneOff[player] += 1;
  return bearingDie(pointNumber, player);
}

function listLegalMoves(state, player, die) {
  const legalMoves = [];
  const closest = closestToExitPoint(state, player);

  if (state.bar[player] > 0) {
    const target = resolveEntryTarget(player, die);
    if (withinBoard(target) && isPointOpen(state, player, target)) {
      legalMoves.push({
        kind: "enter",
        source: "bar",
        target,
        die,
      });
    }
  }

  for (let pointNumber = 1; pointNumber <= POINT_COUNT; pointNumber += 1) {
    const point = state.points[pointNumber - 1];
    if (point.owner !== player || point.count === 0) {
      continue;
    }

    const target = computeTarget(player, pointNumber, die);
    if (withinBoard(target)) {
      if (isPointOpen(state, player, target)) {
        legalMoves.push({
          kind: "move",
          source: pointNumber,
          target,
          die,
        });
      }
      continue;
    }

    const isBearingOff =
      (player === Players.HUMAN && target >= POINT_COUNT + 1) ||
      (player === Players.AI && target <= 0);

    if (!isBearingOff) {
      continue;
    }

    const requiredDie = bearingDie(pointNumber, player);
    if (requiredDie === die) {
      legalMoves.push({
        kind: "bear",
        source: pointNumber,
        target: "off",
        die,
      });
      continue;
    }

    if (
      die > requiredDie &&
      state.bar[player] === 0 &&
      closest !== null &&
      closest === pointNumber
    ) {
      legalMoves.push({
        kind: "bear",
        source: pointNumber,
        target: "off",
        die,
      });
    }
  }

  return legalMoves;
}

function applyMove(state, move, player) {
  if (move.kind === "enter") {
    enterFromBar(state, move.target, player);
    return state;
  }

  if (move.kind === "move") {
    moveChecker(state, move.source, move.target, player);
    return state;
  }

  if (move.kind === "bear") {
    bearOff(state, move.source, player);
    return state;
  }

  throw new Error(`Unknown move kind: ${move.kind}`);
}

function cloneState(state) {
  return {
    points: clonePoints(state.points),
    bar: {
      [Players.HUMAN]: state.bar[Players.HUMAN],
      [Players.AI]: state.bar[Players.AI],
    },
    borneOff: {
      [Players.HUMAN]: state.borneOff[Players.HUMAN],
      [Players.AI]: state.borneOff[Players.AI],
    },
  };
}

const MinigamLogic = {
  Players,
  CHECKERS_PER_PLAYER,
  POINT_COUNT,
  createInitialState,
  cloneState,
  isPointOpen,
  resolveEntryTarget,
  entryDieForTarget,
  computeTarget,
  computeOrigin,
  bearingDie,
  closestToExitPoint,
  hasCheckersBehind,
  enterFromBar,
  moveChecker,
  bearOff,
  listLegalMoves,
  applyMove,
  opposite,
};

if (typeof window !== "undefined") {
  window.MinigamLogic = MinigamLogic;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = MinigamLogic;
}

