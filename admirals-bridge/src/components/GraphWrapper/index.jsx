import React from 'react'
import Graph from '../Graph'
const NUM_PLAYERS = 2

export default class GraphWrapper extends React.Component {
  state = {
    wins: {
      x: ["Player 1", 'Player 2'],
      y: [0, 0], 
      // name: 'Player 1',
      // line: {
      //   width: 5
      // }
      type: 'bar'
    },
    layout: {
      datarevision: 0
    },
    revision: 0,
    isDataUpating: false,
    intervalFunc: null,
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
  
  rand = () => {
    const rawRandom = Math.min(0.99, 2.75 * Math.random()) * NUM_PLAYERS
    return Math.floor(rawRandom)
  }

  increaseGraphic = () => {
    this.setState((state) => {
      const { wins } = state
      const playerWinner = this.rand()
      const previous1 = wins.y[0]
      const previous2 = wins.y[1]
      return {
        revision: this.state.revision + 1,
        wins: {
          ...state.wins,
          y: [previous1 + (playerWinner ? 1 : 0), previous2 + (playerWinner ? 0 : 1)]
        },
        layout: {
          datarevision: this.state.revision + 1
        }
      }
     })
  }

  render() {
    const { wins, layout } = this.state
    return (
      <div>
        <button onClick={this.startStop}>Start / Stop</button>
        <Graph
          data={[wins]}
          layout={layout}
        />
      </div>
    )
  }
}