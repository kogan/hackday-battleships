const BASE_URL = "http://localhost:8645";
export const URLMAP = {
  PLAYERS: `${BASE_URL}/api/player/`,
  BATTLE: `${BASE_URL}/api/battle/`,
};

export const ADMIN_API_TOKEN = process.env.ADMIN_API_TOKEN || "636f47ef285834acb5c729d012a20c56b0107b3c";


export const battleRequest = (player1, player2) => {
  return fetch(URLMAP["BATTLE"], {
    Authorization: `Token ${ADMIN_API_TOKEN}`,
    method: 'POST',
    body: JSON.stringify({
      player1: player1,
      player2, player2,
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
