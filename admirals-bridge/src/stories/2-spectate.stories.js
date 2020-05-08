import React from 'react';
import {Spectate, ResultCell, DisplayPlayer} from '../components/Spectate/index';

export default {
    title: 'ddd',
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

export const BoardDisplay = () => (
    <DisplayPlayer moves={["MISS", "MISS", "MISS", "HIT", "HIT", null, null, "SUNK"]}/>
)