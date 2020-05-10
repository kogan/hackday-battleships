import React from "react";
import Plot from "react-plotly.js";

export default class Graph extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { data, layout } = this.props;
    import("react-plotly.js").then((Plot) => {
      return (
        <Plot
          data={data}
          layout={{
            title: "Win/Loss Plot",
            ...layout,
            autosize: true,
            xaxis: {
              rangemode: "nonnegative",
              gridcolor: "#999",
            },
            yaxis: {
              rangemode: "nonnegative",
              gridcolor: "#999",
            },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: {
              color: "#999",
              family: `"Righteous", Roboto, "Open Sans", arial, sans-serif`,
            },
          }}
          style={{ width: "100%", height: "100%" }}
        />
      );
    });
    return <div>loading...</div>;
  }
}
