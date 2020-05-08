import React from "react";
import Graph from "../Graph";
const NUM_PLAYERS = 2;

const mockState = {
  player1: {
    x: [0],
    y: [0],
    name: "Player 1",
    line: {
      width: 5,
    },
  },
  player2: {
    x: [0],
    y: [0],
    name: "Player 2",
    line: {
      width: 5,
    },
  },
  layout: {
    datarevision: 0,
  },
  revision: 0,
  isDataUpating: false,
  intervalFunc: null,
};

const GraphWrapper = (props) => {
  const [state, setState] = React.useState(mockState);

  const startStop = React.useCallback(() => {
    if (state.isDataUpating) {
      clearInterval(state.intervalFunc);
      setState({
        ...state,
        intervalFunc: null,
        isDataUpating: false,
      });
    } else {
      setState({
        ...state,
        intervalFunc: setInterval(increaseGraphic, 500),
        isDataUpating: true,
      });
    }
  }, []);

  const rand = React.useCallback(() => {
    const rawRandom = Math.min(0.99, 2.75 * Math.random()) * NUM_PLAYERS;
    return Math.floor(rawRandom);
  }, []);

  const increaseGraphic = React.useCallback(() => {
    const { player1, player2, layout, revision } = state;

    const playerWinner = rand();

    const previous1 = player1.y[player1.y.length - 1];
    const previous2 = player2.y[player2.y.length - 1];

    player1.x.push(revision);
    player2.x.push(revision);

    player1.y.push(previous1 + (playerWinner ? 1 : 0));

    player2.y.push(previous2 + (playerWinner ? 0 : 1));

    if (player1.x.length >= 10) {
      player1.x.shift();
      player1.y.shift();
    }
    if (player2.x.length >= 10) {
      player2.x.shift();
      player2.y.shift();
    }
    setState({ ...state, revision: state.revision + 1 });
    layout.datarevision = state.revision + 1;
  }, [state]);

  const { player1, player2, layout } = state;
  return (
    <div>
      <button onClick={startStop}>Start / Stop</button>
      <Graph data={[player1, player2]} layout={layout} />
    </div>
  );
};

export default GraphWrapper;
