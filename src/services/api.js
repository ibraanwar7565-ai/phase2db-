export const BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

async function request(path, options = {}) {
  const url = `${BASE_URL.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    body:
      options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  const responseText = await response.text();
  let data = null;
  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch {
      data = responseText;
    }
  }

  if (!response.ok) {
    const message =
      data?.error?.message ||
      data?.message ||
      (typeof data === "string" ? data : "") ||
      response.statusText ||
      `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}

export const getBudgets = () => request("/budgets");

export const createBudget = (budget) =>
  request("/budgets", { method: "POST", body: budget });

export const updateBudget = (id, budget) =>
  request(`/budgets/${id}`, { method: "PUT", body: budget });

export const deleteBudget = (id) =>
  request(`/budgets/${id}`, { method: "DELETE" });

export const getTransactions = () => request("/transactions");

export const createTransaction = (transaction) =>
  request("/transactions", { method: "POST", body: transaction });

export const deleteTransaction = (id) =>
  request(`/transactions/${id}`, { method: "DELETE" });
