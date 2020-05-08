import React from "react";

import {ADMIN_API_TOKEN as TOKEN} from "./api.js"

const headers = new Headers({
  Authorization: `Token ${TOKEN}`,
});

export const useFetch = (url) => {
  const [isLoading, setIsLoading] = React.useState(null);
  const [response, setResponse] = React.useState(null);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchData = () => {
      setIsLoading(true);
      fetch(url, { headers })
        .then((res) => res.json())
        .then((json) => {
          setResponse(json);
          setIsLoading(false);
        })
        .catch((error) => {
          setError(error);
          setIsLoading(false);
        });
    };
    fetchData();
  }, [url]);

  return { response, error, isLoading };
};
