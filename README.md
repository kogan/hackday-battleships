# Battleships Hackday

## Goal
Each team is to build a battleships AI. The winning team is the team with the most points at the end of the day.

## Teams
The "Intelligence Officers" will be working in pairs to design an AI and to interface with the battleships engine.

In addition to the Intelligence Officers, we’re going to need some "Marine Engineers".

A team of 4 Engineers will work to come up with a beautiful front end and spectator mode for the battles, so we can see the results at the end of the day.
The Engineers are also responsible for getting the engine deployed into the cloud.

If there's time, the Officers and Engineers may work together to build a human version of the game.

## Scoring
The team with the greatest score wins, being crowned Admirals of the Sea.

#### Head To Head
Each team will verse each other team once. 2 points for a victory, 1 point for a draw, 0 points for a loss.
Head to Head configuration is:

10x10 grid, 1 Destroyer, 1 Frigate, 2 Submarines and 1 Patrol Boat.

#### Ships That Scale
Each team will battle the same, random setup in a quest for the fewest moves.

4 points to the winner of each category.

 - 10x10 grid: 1 Frigate, 2 Submarines, 3 Patrol Boats, 4 Minehunters.
 - 30x30 grid: 2 Destroyers, 2 Frigates, 4 Submarines, 2 Patrol Boats.
 - 10x10 grid: 4 Submarines.
 - 20x20 grid: 10 Minehunters, 1 Frigate.

#### Best design
Subjectively, the builders will collectively nominate the coolest AI for an extra point.

## Rules
 - You cannot place ships adjacent to one another.
 - You get another turn if you "HIT" an enemy ship.
 - You are notified if a "HIT" is the last one one the ship ("SUNK").
 - You cannot make the same attack twice.
 - You cannot place a ship out of bounds.

For a visualisation of how the setup works, play around with [this](http://en.battleship-game.org/).

## Schedule
 - 9:00am: introduction
 - 9:15am: HACK
 - 12:30pm: lunch
 - 1:30pm: back to the grind
 - 4:30pm: begin battles
 - 5:00pm: discuss strategies
 - 5:30pm: Head ~~to the pub~~ back into self isolation
 
## Engine API

### Overview

A Game can be in a number of states:
 - join
 - setup
 - attack
 - finished
 
#### Join phase
 - Users are able to join this game.
 - A User cannot join a game they've already joined (can't play against yourself).
 - Once a second User has joined, the Game automatically moves to the `setup` phase.
 
#### Setup phase
 - Users may place ships
 - Once both players have placed their ships, the Game automatically moves to the `attack` phase.
 
#### Attack phase
Attacks are asynchronous. You won't see what your opponent plays until after the game is complete.

 - Users may start their attacks
 - Once both players have found all enemy ships, the Game automatically moves to the `finished` phase.
 
#### Finished phased
 - Users may query the Game to see who won

### Endpoints

#### Create a game
`POST /api/game/create/` 

Request

```
{
  board_size: Integer (optional, default=10)
  ship_config: [
    {
      length: Integer (required)
      count: Integer (required)
    }
  ] (required)
}
```

Response

```
{
  game_id: String
}
```

### Query game state
`GET /api/game/<game_id/`

#### Join a game
`POST /api/game/<game_id>/join/`

#### Place your ships
`POST /api/game/<game_id>/place/`

Request

```
[{
  x: Integer (required)
  y: Integer (required)
  length: Integer (required)
  orientation: "HORIZONTAL"|"VERTICAL" (required)
}]
```

#### Make an attack
`POST /api/game/<game_id>/attack/`

Request

```
{
  x: Integer (required)
  y: Integer (required)
}
```

Response

```
{
  x: Integer
  y: Integer
  result: "MISS"|"HIT"|"SUNK"
}
```

## Glossary

*Ships*

| Name | Length |
|------| -------|
|Minehunter|1|
|Patrol Boat|2|
|Submarine|3|
|Frigate|4|
|Destroyer|5|
