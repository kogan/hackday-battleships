import React from 'react'
import Graph from '../Graph'
const NUM_PLAYERS = 2
const STOP = 60

export default class GraphWrapper extends React.Component {
  state = {
    wins: {
      x: ["Player 1", 'Player 2'],
      y: [0, 0],
      type: 'bar',
      text: ["0", "0"],
      textposition: 'auto',
      textfont: {
        size: 20
      },
      marker: {
        color: 'rgb(30,72,30)',
        opacity: 0.7,
        line: {
          color: 'white',
          width: 1.5
        }
      }
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
      const { wins, revision } = state
      if(revision >= STOP) {
        return { 
          intervalFunc: null,
          isDataUpating: false
        }
      }
      const playerWinner = this.rand()
      const previous1 = wins.y[0]
      const previous2 = wins.y[1]
      const y = [previous1 + (playerWinner ? 1 : 0), previous2 + (playerWinner ? 0 : 1)]
      return {
        revision: revision + 1,
        wins: {
          ...wins,
          y,
          text: y.map(String)
        },
        layout: {
          datarevision: revision + 1
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