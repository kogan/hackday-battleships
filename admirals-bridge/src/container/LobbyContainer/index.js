import React from "react";
import styled from 'styled-components'

const ScreenBackground = styled.div`
  max-width: 619px;
  border: solid 3px #40a692;
  background-color: rgba(21, 30, 27, 0.9);
  padding: 12px;
  margin: 0 auto;
  margin-top: 100px;

  h1 {
    color: white;
  }
`

const LobbyContainer = ({children}) => (
  <ScreenBackground>
    <h1>Battleship</h1>
    {children}
  </ScreenBackground>
)

export default LobbyContainer;
