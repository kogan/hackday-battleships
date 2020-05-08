import React from "react";
import { StateContext } from "../../App";

const MatchMaker = () => {
  const {selectedPlayers, config} = React.useContext(StateContext);

  if (selectedPlayers.length == 0) {
    return <div>Please select player to battle in the settings first.</div>
  }

  return (
    <div>
      <h1>{selectedPlayers[0]} vs {selectedPlayers[1]}</h1>
      Prepare Your Battleships!
      Ready to launch {config.turns} turns battle.
    </div>
  )
}

export default MatchMaker;
