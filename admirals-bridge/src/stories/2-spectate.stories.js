import React from 'react';
import {Spectate, ResultCell, DisplayPlayer, stateToBoard} from '../components/Spectate/index';

export default {
    title: 'Spectator Views',
    component: Spectate,
  };

export const SpectateView = () => (
    <Spectate />
)

export const CellMiss = () => (
    <div style={{width: "200px", height: "200px"}}>
        <ResultCell result={"MISS"} />
    </div>
)

export const CellHit = () => (
    <div style={{width: "200px", height: "200px"}}>
        <ResultCell result={"HIT"} />
    </div>
)

export const BoardDisplayDummy = () => (
    <DisplayPlayer moves={["MISS", "MISS", "MISS", "HIT", "HIT", null, null, "SUNK"]}/>
)

const samplePlayerState = stateToBoard([{"x":0,"y":0,"player":"player1","result":"HIT"},
                                        {"x":0,"y":5,"player":"player1","result":"SUNK"},
                                        {"x":3,"y":3,"player":"player1","result":"MISS"}
                                    ], "player1")

export const BoardDisplayWithState = () => (
    <DisplayPlayer moves={samplePlayerState}/>
)
