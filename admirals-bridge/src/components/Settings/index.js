import React from "react";
import styled from "styled-components";
import Button from "../Button";
import { StateContext } from "../../App";

const PageHeader = styled.h2`
  font-size: 24px;
  text-align: left;
`;

const SettingsContainer = styled.div`
  padding: 30px 80px;
`;

const SettingsRow = styled.section`
  display: flex;
  align-items: center;
  margin-bottom: 30px;
`;

const SettingsHeader = styled.h4`
  margin: 0 48px 0 0;
  min-width: 15%;
  text-align: left;
`;

const SettingsDropdown = styled.select`
  padding: 10px 16px;
  border: solid 1px #40a692;
  background-color: #1b2b28;
  color: #fff;
`;

const TURN_OPTIONS = [1, 10, 100, 1000];

const Settings = ({ selectPlayer, setTurns }) => {
  const { players, selectedPlayers, config } = React.useContext(StateContext);

  const handleSetTurns = (e) => {
    setTurns(e.target.value);
  };

  return (
    <>
      <PageHeader>Settings</PageHeader>
      <SettingsContainer>
        <SettingsRow>
          <SettingsHeader>Player</SettingsHeader>
          {Array.isArray(players) &&
            players.map((player) => (
              <Button
                key={player.name}
                active={selectedPlayers.includes(player.name)}
                onClick={() => selectPlayer(player.name)}
              >
                {player.name}
              </Button>
            ))}
        </SettingsRow>
        <SettingsRow>
          <SettingsHeader>Turns</SettingsHeader>
          <SettingsDropdown
            onChange={handleSetTurns}
            defaultValue={config.turns}
          >
            {TURN_OPTIONS.map((value) => (
              <option value={value} key={value}>
                {value}
              </option>
            ))}
          </SettingsDropdown>
        </SettingsRow>
      </SettingsContainer>
    </>
  );
};

export default Settings;
