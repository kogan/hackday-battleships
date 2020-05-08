import React from "react";
import styled from "styled-components";

const ScreenBackground = styled.div`
  max-width: 619px;
  border: solid 3px #40a692;
  background-color: rgba(21, 30, 27, 0.9);
  padding: 24px 36px;
  margin: 0 auto;
  margin-top: 100px;
  color: #fff;
  position: relative;

  h1 {
    font-family: "Righteous";
    text-transform: uppercase;
    text-align: left;
    font-size: 48px;
    margin-top: 0;
  }
`;

const LobbyContainer = ({ children }) => (
  <ScreenBackground>{children}</ScreenBackground>
);

export default LobbyContainer;
