import React from 'react'
import Plot from 'react-plotly.js'
import ship from '../../images/resting-ship.svg'

export default class Graph extends React.Component {
  
  render() {
    const { data, layout } = this.props
    const player1Y = data[0].y[0]
    const player2Y = data[0].y[1]
    return (
      <Plot
        data={data}
        layout={{
          title: 'Win/Loss Plot',
          ...layout,
          images: [
            {
              "source": ship,
              "xref": "x",
              "yref": "paper",
              "x": 0,
              "y": player1Y / 50,
              "sizex": 0.3,
              "sizey": 0.3,
              "xanchor": "center",
              "yanchor": "bottom"
            },
            {
              "source": ship,
              "xref": "x",
              "yref": "paper",
              "x": 1,
              "y": player2Y / 50,
              "sizex": 0.3,
              "sizey": 0.3,
              "xanchor": "center",
              "yanchor": "bottom"
            }
          ],
          autosize: true,
          xaxis: {
            gridcolor: "#999",
            showgrid: false,
          },
          yaxis: {
            range: [0, 50],
            gridcolor: "#999",
            showgrid: false,
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