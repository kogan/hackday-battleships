import React from 'react'
import Plot from 'react-plotly.js'
import Graph from './Graph'
import rawData from './rawData'
const NUM_PLAYERS = 2

export default class GraphWrapper extends React.Component {
  state = {
    player1: {
      x: [0],
      y: [0], 
      name: 'Player 1'
    },
    player2: {
      x: [0],
      y: [0],
      name: 'Player 2'
    },
    layout: {
      datarevision: 0
    },
    revision: 0,
    isDataUpating: false,
    intervalFunc: null,
  }
  constructor(props) {
    super(props)
  }

  startStop = () => {
    if(this.state.isDataUpating) {
      this.setState((state) => {
        clearInterval(state.intervalFunc)
        return { 
          intervalFunc: null,
          isDataUpating: false
        }
      })
    }
    else {
      this.setState({
        intervalFunc: setInterval(this.increaseGraphic, 500),
        isDataUpating: true
      })
    }
  }
  
  rand = () => parseInt(Math.random() * NUM_PLAYERS)

  increaseGraphic = () => {
    const { player1, player2, layout, revision } = this.state;

    const playerWinner = this.rand()
  
    const previous1 = player1.y[player1.y.length-1]
    const previous2 = player2.y[player2.y.length-1]

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
    this.setState({ revision: this.state.revision + 1 });
    layout.datarevision = this.state.revision + 1;
  }

  render() {
    const { player1, player2, layout } = this.state
    return (
      <div>
        <Graph
          data={[
            player1,
            player2
          ]}
          layout={layout}
        />
        <button onClick={this.startStop}>Start / Stop</button>
      </div>
    )
  }
}