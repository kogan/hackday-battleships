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

function stateToBoard(state, player) {
    let results = []
    for(let x = 0; x < 10; x++) {
        for(let y = 0; y < 10; y++) {
        let toAppend = state.filter((item) => item.x == x && item.y == y && item.player == player)
        if (toAppend.length === 1){
            console.log("found one!")
            results.push(toAppend[0].result)
            }
        else {
            results.push(null)
        }
        }
    }
    console.log(results)
    return results
}

export {Spectate, ResultCell, DisplayPlayer, stateToBoard};
