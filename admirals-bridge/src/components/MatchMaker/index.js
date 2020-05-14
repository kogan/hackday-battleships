import React, {Fragment} from "react";
import styled from "styled-components";
import Button from "../Button";
import {battleRequest} from '../../api.js'
import { Link, useHistory } from "react-router-dom";
import { StateContext } from "../../App";

const VersusHeader = styled.h1`
  && {
    margin: 0 auto;
    text-align: center;
    margin-bottom: 12px;

    span {
      font-size: 24px;
    }
  }
`


const MatchMaker = () => {
  const {selectedPlayers, config} = React.useContext(StateContext);
  const [error, setError] = React.useState("");
  let history = useHistory()

  const onBattleClick = () => {
    battleRequest(selectedPlayers[0], selectedPlayers[1]).then(result => {
      if (result) {
        console.log("Battle successfully launched")
        history.push('/results')
      } else {
        setError("Failure in launching battle.. Please see error")
      }
    })
  }

  if (selectedPlayers.length === 0) {
    return (
      <Fragment>
        Please select player to battle in the settings first.
        <div>
          <Link to="/settings/">
            <Button style={{marginTop: '12px'}}>Settings</Button>
          </Link>
        </div>
      </Fragment>
    )
  }

  return (
    <div>
      <VersusHeader>{selectedPlayers[0]} <span>vs</span> {selectedPlayers[1]}</VersusHeader>
      Prepare Your Battleships!
      Ready to launch {config.turns} turns battle.
      <div>
        <Button onClick={onBattleClick} style={{marginTop: '12px'}}>Battle!</Button>
      </div>
      <p style={{color: 'red'}}>{error}</p>
    </div>
  )
}

export default MatchMaker;
