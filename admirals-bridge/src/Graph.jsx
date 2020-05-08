import React from 'react'
import Plot from 'react-plotly.js'

export default class Graph extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    const { data, layout } = this.props
    return (
      <Plot
        data={data}
        layout={{ title: 'Win/Loss Plot', ...layout, width: 800, height: 600 }}
      />
    )
  }
}