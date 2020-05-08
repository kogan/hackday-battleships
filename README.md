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
 - 9:15am: introduction
 - 9:30am: HACK
 - 12:30pm: lunch
 - 1:30pm: back to the grind
 - 4:30pm: begin battles
 - 5:00pm: discuss strategies
 - 5:30pm: Head ~~to the pub~~ back into self isolation

## Architecture

Each bot will use a subdirectory in this project.
Each bot will need to expose an HTTP interface via a Dockerfile (see `example_client`).
Wire up your bot to the `docker-compose` file, using `player1` as an example.


## Dev setup

start all the useful containers.

`docker-compose up -d django db dispatcher`

Run migrations for the first time.

`./shortcuts.sh migrate`

Create an admin user for yourself.

`./shortcuts.sh createsuperuser`

Log in to the admin: http://localhost:8645/admin/

Create 2 additional users in the admin interface.

Create Tokens for each of those users, and export them as ENV vars:

```
export GAME_TOKEN_P1=<token>
export GAME_TOKEN_P2=<token>
```

Create a game config with the default configuration:
boardsize: 10

```
[{"length":5, "count":1}, {"length":4, "count":1}, {"length":3, "count":2}, {"length":2, "count":1}]
```

Create BotServers for each of your player
(use http://player1/ and http://player2/ respectively)

Start up the example clients
`docker-compose up -d player1 player2`

Start the game via shell:

```
./shortcuts.sh shell
cfg = GameConfig.objects.first()
p1 = BotServer.objects.get(user__username='player1')
p2 = BotServer.objects.get(user__username='player2')

GameConfig.objects.start_game(cfg.id, p1, p2)
```


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

### Query game state
`GET /api/game/<game_id/`

Response

```
{
  state: "join"|"setup"|"attack"|"finished"
  id: String
  moves: Optional[
  {
    x: Integer
    y: Integer
    player: String
    result: String
  }]
  is_draw: Optional[Boolean]
  loser: Optional[String]
```

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

*Coordinate system*

Consider the following board:

|   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 |   |   |   |   |   |   |   |   |   |   |
| 1 |   |   | S | S | S |   |   |   |   |   |
| 2 |   |   |   |   |   |   |   |   |   |   |
| 3 |   |   |   |   |   |   |   |   |   |   |
| 4 |   |   |   |   |   |   |   |   |   |   |
| 5 |   |   |   |   |   |   | F |   |   |   |
| 6 |   |   |   |   |   |   | F |   |   |   |
| 7 |   |   |   |   |   |   | F |   |   |   |
| 8 |   |   |   |   |   |   | F |   |   |   |
| 9 | P | P |   |   |   |   |   |   |   |   |

The `Submarine` is at position `(x=2, y=1, length=3, orientation=HORIZONTAL)`

The `Frigate` is at position `(x=6, y=5, length=4, orientation=VERTICAL)`

The `Patrol Boat` is at position `(x=0, y=9, length=2 orientation=HORIZONTAL)`


## Cloud shell

An environment variable `GOOGLE_APPLICATION_CREDENTIALS` needs to be set pointing to your credentials.
These credentials can be generated with the command:

`gcloud auth application-default login`
`EXPORT GOOGLE_APPLICATION_CREDENTIALS=/path/to/application_default_credentials.json`

(This is most commonly `~/.config/gcloud/application_default_credentials.json`)

It would be a good idea to put that in your `.bashrc`.

You'll also need to configure docker to be able to talk to GCR.

`gcloud auth configure-docker`

`cloudshell.py` allows connectivity with a Django shell as well as a PSQL client for production and UAT environments.

`./cloudshell.py --project <project> [shell|psql]`
