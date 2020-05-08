const express = require("express");
const axios = require("axios");
const app = express();

app.use(express.json());

const promiseWithTimeout = (timeoutMs, promise) => {
  return Promise.race([
    promise(),
    new Promise((resolve, reject) => setTimeout(() => reject(), timeoutMs))
  ]);
};

const notifyPlayer = async ({ server_url, username }, game_id, url) => {
  try {
    await promiseWithTimeout(30 * 1000, () =>
      axios.post(server_url, { game_id, url })
    );
    return { username, state: "finished" };
  } catch (e) {
    return { username, state: "dnf" };
  }
};

app.post("/", async (req, res) => {
  // requests come in.

  // wait for the 2 players
  const { players, game_id, callback_url, secret } = req.body;
  if (!players || !game_id || !callback_url) {
    res.sendStatus(400);
    res.send();
    return;
  }
  // immediately respond to requester.
  res.send();
  // dispatch the game id to the 2 players and wait
  const results = await Promise.all(
    players.map(p => notifyPlayer(p, game_id, callback_url))
  );

  // send results back to server
  axios.post(`${callback_url}/api/game/${game_id}/finish/`, {
    players: results,
    secret
  });
});

const PORT = process.env.PORT;
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}...`);
});
