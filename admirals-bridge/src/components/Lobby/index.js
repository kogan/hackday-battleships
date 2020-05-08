import React, { Fragment } from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";

const MenuButton = styled.div`
  border: solid 3px #40a692;
  background-color: rgba(21, 30, 27, 0.9);
  padding: 12px;
  color: white;
  width: 50%;
  margin: 12px auto;
  font-family: 'Roboto', sans-serif;
  font-size: 14px;
  text-transform: uppercase;
  &:hover {
    background-color: #40a692;
  }
`;

const Lobby = () => (
  <Fragment>
    <h1>Battleship</h1>
    <Link to="/match/">
      <MenuButton>Start</MenuButton>
    </Link>
    <Link to="/results/">
      <MenuButton>Battle Results</MenuButton>
    </Link>
    <Link to="/settings/">
      <MenuButton>Settings</MenuButton>
    </Link>
  </Fragment>
);

export default Lobby;
