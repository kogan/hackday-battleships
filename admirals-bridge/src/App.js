import React from "react";
import styled from "styled-components";
import { BrowserRouter as Router, Switch, Route, Link } from "react-router-dom";
import LobbyContainer from "./container/LobbyContainer";
import Lobby from "./components/Lobby";
import MatchMaker from "./components/MatchMaker";
import Results from "./components/Results";
import Settings from "./components/Settings";
import "./App.css";

import { useFetch } from "./hooks";
import { URLMAP } from "./api";

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
`;

function Navigator() {
  return (
    <NavbarUl>
      <li>
        <Link to="/">Lobby</Link>
      </li>
      <li>
        <Link to="/match/">Battle!</Link>
      </li>
      <li>
        <Link to="/results/">Results</Link>
      </li>
      <li>
        <Link to="/settings/">Settings</Link>
      </li>
    </NavbarUl>
  );
}

const initialState = {
  players: [],
  selectedPlayers: [],
  config: {
    turns: 1,
  },
};
export const StateContext = React.createContext(initialState);

function App() {
  const [state, setState] = React.useState(initialState);

  const selectPlayer = (name) => {
    if (state.selectedPlayers.includes(name)) return;
    setState({
      ...state,
      selectedPlayers: [name, ...state.selectedPlayers].slice(0, 2),
    });
  };

  const setTurns = (turns) => {
    if (state.config.turns === turns) return;
    setState({
      ...state,
      config: {
        ...state.config,
        turns: parseInt(turns, 10),
      },
    });
  };

  const { response } = useFetch(URLMAP.PLAYERS);

  React.useEffect(() => {
    if (response) {
      setState({
        ...state,
        players: response,
      });
    }
  }, [response, setState, state]);
  return (
    <StateContext.Provider value={state}>
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
              <Route exact path="/settings/">
                <Settings selectPlayer={selectPlayer} setTurns={setTurns} />
              </Route>
              <Route exact path="/results/">
                <Results />
              </Route>
            </Switch>
          </LobbyContainer>
        </div>
      </Router>
    </StateContext.Provider>
  );
}

export default App;
