function error(message) {
  return JSON.stringify({ error: message });
}

function outputFields(entry) {
  if (!entry || typeof entry !== "object") return {};
  const output = {};
  for (const field of ["id", "title", "lyric"]) {
    if (typeof entry[field] === "string") output[field] = entry[field];
  }
  for (const field of ["audio_url", "image_url", "video_url"]) {
    if (typeof entry[field] === "string" && /^https:\/\/[^\s]+$/i.test(entry[field])) output[field] = entry[field];
  }
  if (typeof entry.duration === "number") output.duration = entry.duration;
  return output;
}

module.exports.runtime = {
  handler: async function ({ task_id } = {}) {
    const configuredToken = this.runtimeArgs?.ACEDATACLOUD_API_TOKEN;
    const token = typeof configuredToken === "string" ? configuredToken.trim() : "";
    if (!token || /\s/.test(token)) return error("Set the Ace Data Cloud API token in the skill settings.");
    const id = typeof task_id === "string" ? task_id.trim() : "";
    if (!/^[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}$/i.test(id)) {
      return error("Enter a Suno task ID returned by Ace Data Cloud.");
    }

    try {
      const response = await fetch("https://api.acedata.cloud/suno/tasks", {
        method: "POST",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id: id.toLowerCase(), action: "retrieve" }),
        signal: AbortSignal.timeout(15000),
        redirect: "error",
      });
      if (!response.ok) return error(`Suno task lookup failed (HTTP ${response.status}).`);
      const task = await response.json();
      if (typeof task?.id !== "string" || task.id.toLowerCase() !== id.toLowerCase()) {
        return error("Suno returned a different task or an unexpected response.");
      }
      if (typeof task.finished_at !== "number" || task.finished_at <= 0) {
        const status = typeof task.started_at === "number" && task.started_at > 0 ? "running" : "pending";
        return JSON.stringify({ task_id: task.id, status });
      }
      const result = typeof task.response === "string" ? JSON.parse(task.response) : task.response;
      if (result?.task_id && (typeof result.task_id !== "string" || result.task_id.toLowerCase() !== id.toLowerCase())) {
        return error("Suno returned a result for a different task.");
      }
      if (result?.success === false) return JSON.stringify({ task_id: task.id, status: "failed" });
      if (result?.success !== true || !Array.isArray(result.data)) return error("Suno returned an unexpected result.");
      const outputs = result.data.map(outputFields).filter((entry) => Object.keys(entry).length > 0);
      return JSON.stringify({ task_id: task.id, status: "succeeded", outputs });
    } catch {
      return error("Suno could not complete the task lookup.");
    }
  },
};
