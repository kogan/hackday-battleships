const BASE_URL = "http://localhost:8645";
export const URLMAP = {
  PLAYERS: `${BASE_URL}/api/player/`,
  BATTLE: `${BASE_URL}/api/game/battle/`,
  GAMES: `${BASE_URL}/api/games/`,
  GAME: id => `${BASE_URL}/api/games/${id}`,
};

export const ADMIN_API_TOKEN = process.env.ADMIN_API_TOKEN || "636f47ef285834acb5c729d012a20c56b0107b3c";


export const battleRequest = (player1, player2) => {
  return fetch(URLMAP["BATTLE"], {
    headers: {
      "Authorization": `Token ${ADMIN_API_TOKEN}`,
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    method: 'POST',
    body: JSON.stringify({
      "player_1": player1,
      "player_2": player2,
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error("Failure triggering battle")
    }
    return Promise.resolve(true)
  })
  .catch(error => {
    console.error("Failure triggering battle")
    return Promise.resolve(false)
  });
}
