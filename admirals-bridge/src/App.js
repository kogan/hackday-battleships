import React from "react";
import { BrowserRouter as Router, Switch, Route, Link } from "react-router-dom";
import Lobby from "./components/Lobby";
import MatchMaker from "./components/MatchMaker";
import Results from "./components/Results";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="App">
        <ul>
          <li>
            <Link to="/">Lobby</Link>
          </li>
          <li>
            <Link to="/match/">Match Maker</Link>
          </li>
          <li>
            <Link to="/results/">Results</Link>
          </li>
        </ul>
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
      </div>
    </Router>
  );
}

export default App;
