const BASE_URL = "http://localhost:8645";
export const URLMAP = {
  PLAYERS: `${BASE_URL}/api/player/`,
  BATTLE: `${BASE_URL}/api/battle/`,
};

export const ADMIN_API_TOKEN =
  process.env.ADMIN_API_TOKEN || "afd8914c0f34d84e5f59bbd780e1b1ae78668ea7";

export const battleRequest = (player1, player2) => {
  return fetch(URLMAP["BATTLE"], {
    Authorization: `Token ${ADMIN_API_TOKEN}`,
    method: "POST",
    body: JSON.stringify({
      player1: player1,
      player2,
      player2,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failure triggering battle");
      }
      return Promise.resolve(true);
    })
    .catch((error) => {
      console.error("Failure triggering battle");
      return Promise.resolve(false);
    });
};
