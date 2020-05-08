import React from "react";
import styled from 'styled-components'

const HitCell = styled.div`
  background-color: red;
  width: 100%;
  height: 100%;
`
const MissedCell = styled.div`
  background-color: blue;
  width: 100%;
  height: 100%;
`
const SunkCell = styled.div`
  background-color: black;
  width: 100%;
  height: 100%;
`
const DefaultCell = styled.div`
    background-color: green;
    width: 100%;
    height: 100%;
`

const GameGrid = styled.div`
    display: grid;
    background-color: grey;
    border: 5px solid grey;
    border-radius: 5px;
    grid-template-columns: repeat(10, 1fr);
    grid-template-rows: repeat(10, 1fr);
    width: 500px;
    height: 500px;
    grid-gap: 5px;
`


const Spectate = () => <div>Spectate</div>;

function ResultCell({result}) {
    let comp = null;
    switch (result) {
        case "HIT":
            comp = <HitCell />
            break;
        case "MISS":
            comp = <MissedCell />
            break;
        case "SUNK":
            comp = <SunkCell />
            break;
        default:
            comp = <DefaultCell />
    }
    return (comp)
}

function displayResult(result) {
    return <ResultCell result={result}/>
}

function DisplayPlayer({moves}) {
    return (
        <GameGrid>{
            moves.map(displayResult)
        }
        </GameGrid>
    )
}

export {Spectate, ResultCell, DisplayPlayer};

function gameStateToPlayerView(apiResult) {
    
}