function error(message) {
  return JSON.stringify({ error: message });
}

module.exports.runtime = {
  handler: async function ({ query, country = "us", language = "en" } = {}) {
    const configuredToken = this.runtimeArgs?.ACEDATACLOUD_API_TOKEN;
    const token = typeof configuredToken === "string" ? configuredToken.trim() : "";
    if (!token || /\s/.test(token)) return error("Set the Ace Data Cloud API token in the skill settings.");
    if (typeof query !== "string" || !query.trim() || query.trim().length > 2048) {
      return error("Enter a search query of 1 to 2048 characters.");
    }
    if (typeof country !== "string" || !/^[a-z]{2}$/i.test(country) ||
        typeof language !== "string" || !/^[a-z]{2,3}(?:-[a-z]{2,4})?$/i.test(language)) {
      return error("Enter a country code and a language code, such as us and en.");
    }

    const search = query.trim();
    try {
      const response = await fetch("https://api.acedata.cloud/serp/google", {
        method: "POST",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: search, type: "search", country: country.toLowerCase(), language, number: 5 }),
        signal: AbortSignal.timeout(15000),
        redirect: "error",
      });
      if (!response.ok) return error(`Google Search request failed (HTTP ${response.status}).`);
      const data = await response.json();
      if (!data || !Array.isArray(data.organic)) return error("Google Search returned an unexpected response.");
      const results = data.organic
        .filter((entry) => typeof entry?.title === "string" && typeof entry.link === "string" && /^https?:\/\/[^\s]+$/i.test(entry.link))
        .slice(0, 5)
        .map(({ title, link, snippet }) => ({ title, link, snippet: typeof snippet === "string" ? snippet : "" }));
      return JSON.stringify({ query: search, results });
    } catch {
      return error("Google Search could not complete the request.");
    }
  },
};
