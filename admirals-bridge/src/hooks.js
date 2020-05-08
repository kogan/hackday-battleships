import React from "react";

const TOKEN = "afd8914c0f34d84e5f59bbd780e1b1ae78668ea7";

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
