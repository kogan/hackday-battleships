import React from "react";
import styled from 'styled-components'
import { BrowserRouter as Router, Switch, Route, Link } from "react-router-dom";
import LobbyContainer from "./container/LobbyContainer";
import Lobby from "./components/Lobby";
import MatchMaker from "./components/MatchMaker";
import Results from "./components/Results";
import "./App.css";

function Navigator() {
  const NavbarUl = styled.ul`
    list-style-type: none;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background-color: #333;

    li {
      float: left;
      a {
        display: block;
        color: white;
        text-align: center;
        padding: 14px 16px;
        text-decoration: none;
      }
      a:hover {
        background-color: #111;
      }
    }
  `
  return (
    <NavbarUl>
      <li>
        <Link to="/">Lobby</Link>
      </li>
      <li>
        <Link to="/match/">Match Maker</Link>
      </li>
      <li>
        <Link to="/results/">Results</Link>
      </li>
    </NavbarUl>
  )
}

function App() {
  return (
    <Router>
      <div className="App">
        <Navigator />
        <LobbyContainer>
          <Switch>
            <Route exact path="/">
              <Lobby />
            </Route>
            <Route exact path="/match/">
              <MatchMaker />
            </Route>
            <Route exact path="/results/">
              <Results />
            </Route>
          </Switch>
        </LobbyContainer>
      </div>
    </Router>
  );
}

export default App;
