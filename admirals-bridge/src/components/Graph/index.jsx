import React from 'react'
import Plot from 'react-plotly.js'
import ship from '../../images/resting-ship.svg'

export default class Graph extends React.Component {
  
  render() {
    const { data, layout } = this.props
    // const { player1, player2, layout } = this.props
    const player1Y = data[0].y[0]
    const player2Y = data[0].y[1]
    // const player1Y = player1.y[player1.y.length-1]
    // const player2X = player2.x[player2.x.length-1]
    // const player2Y = player2.y[player2.y.length-1]
    // console.log(`player1X, player1Y, player2X, player2Y => `, player1X, player1Y, player2X, player2Y)
    // console.log(`player1Y, player2Y => `, player1Y, player2Y)
    return (
      <Plot
        // data={[
        //   player1,
        //   player2,
        // ]}
        data={data}
        layout={{
          title: 'Win/Loss Plot',
          ...layout,
          images: [
            {
              "source": ship,
              "xref": "paper",
              "yref": "paper",
              "x": 0.25,
              "y": player1Y / 50,
              "sizex": 0.3,
              "sizey": 0.3,
              "xanchor": "center",
              "yanchor": "bottom"
            },
            {
              "source": "https://images.plot.ly/language-icons/api-home/js-logo.png",
              "xref": "x",
              "yref": "y",
              "x": 0.75,
              "y": player2Y,
              "sizex": 1,
              "sizey": 1,
              "xanchor": "center",
              "yanchor": "center"
            }
          ],
          autosize: true,
          xaxis: {
            rangemode: "nonnegative",
            gridcolor: "#999"
          },
          yaxis: {
            range: [0, 50],
            gridcolor: "#999"
          },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: {
            color: "#999",
            family: `"Righteous", Roboto, "Open Sans", arial, sans-serif`

          }
        }}
        style={{ width: '100%', height: '100%'}}
      />
    )
  }
}