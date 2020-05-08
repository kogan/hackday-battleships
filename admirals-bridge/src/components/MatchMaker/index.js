import React from "react";
import { useFetch } from "../../hooks";
import { URLMAP } from "../../api";

const MatchMaker = () => {
  const { isLoading, response, error } = useFetch(URLMAP.PLAYERS);
  if (isLoading) {
    return <div>...Loading...</div>;
  } else if (error) {
    return <div>{error.toString()}</div>;
  } else if (response) {
    return (
      <>
        <div>MatchMaker</div>
        <ul>
          {response.map((player) => (
            <li>{player.name}</li>
          ))}
        </ul>
      </>
    );
  }

  return <div>Prepare Your Battleships</div>;
};

export default MatchMaker;
