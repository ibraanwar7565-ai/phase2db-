import React, { useEffect, useState } from "react";
import FormField from "../components/FormField";
import {
  getBudgets,
  createBudget,
  updateBudget,
  deleteBudget,
} from "../services/api";
import "../styles/theme.css";

export default function BudgetPage() {
  const [budgets, setBudgets] = useState([]);
  const [form, setForm] = useState({
    name: "",
    amount: "",
    period: "monthly",
    category: "",
  });
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadBudgets() {
    try {
      const data = await getBudgets();
      setBudgets(Array.isArray(data) ? data : data?.budgets ?? []);
    } catch (error) {
      setMessage(`Could not load budgets: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBudgets();
  }, []);

  const updateField = (field) => (event) => {
    setForm((previous) => ({
      ...previous,
      [field]: event.target.value,
    }));
  };

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");

    if (!form.name.trim() || Number(form.amount) <= 0) {
      setMessage("Enter a budget name and an amount greater than zero.");
      return;
    }

    const payload = {
      ...form,
      amount: Number(form.amount),
    };

    try {
      if (editingId !== null) {
        await updateBudget(editingId, payload);
        setMessage("Budget updated successfully.");
      } else {
        await createBudget(payload);
        setMessage("Budget created successfully.");
      }

      setForm({
        name: "",
        amount: "",
        period: "monthly",
        category: "",
      });
      setEditingId(null);
      await loadBudgets();
    } catch (error) {
      setMessage(`Could not save budget: ${error.message}`);
    }
  }

  function startEditing(budget) {
    setEditingId(budget.id);
    setForm({
      name: budget.name ?? "",
      amount: String(budget.amount ?? ""),
      period: budget.period ?? "monthly",
      category: budget.category ?? "",
    });
    setMessage("");
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this budget?")) return;

    try {
      await deleteBudget(id);
      setMessage("Budget deleted successfully.");
      await loadBudgets();
    } catch (error) {
      setMessage(`Could not delete budget: ${error.message}`);
    }
  }

  return (
    <main className="sp-page">
      <header className="sp-page__header">
        <p className="sp-page__eyebrow">SmartPesa</p>
        <h1 className="sp-page__title">Budgets</h1>
        <p className="sp-page__description">
          Create and manage your spending limits.
        </p>
      </header>

      <section className="sp-card">
        <form className="sp-form" onSubmit={handleSubmit}>
          <FormField
            id="budget-name"
            label="Budget name"
            value={form.name}
            onChange={updateField("name")}
            placeholder="e.g. Groceries"
            required
          />

          <div className="sp-form__row">
            <FormField
              id="budget-amount"
              label="Amount (KES)"
              type="number"
              value={form.amount}
              onChange={updateField("amount")}
              min="0.01"
              step="0.01"
              required
            />

            <FormField
              id="budget-period"
              label="Period"
              as="select"
              value={form.period}
              onChange={updateField("period")}
              options={[
                { value: "weekly", label: "Weekly" },
                { value: "monthly", label: "Monthly" },
                { value: "yearly", label: "Yearly" },
              ]}
              required
            />
          </div>

          <FormField
            id="budget-category"
            label="Category"
            value={form.category}
            onChange={updateField("category")}
            placeholder="e.g. Food"
          />

          {message && <p className="sp-alert" role="status">{message}</p>}

          <div className="sp-form__row">
            <button className="sp-button" type="submit">
              {editingId !== null ? "Update budget" : "Create budget"}
            </button>

            {editingId !== null && (
              <button
                className="sp-button"
                type="button"
                onClick={() => {
                  setEditingId(null);
                  setForm({
                    name: "",
                    amount: "",
                    period: "monthly",
                    category: "",
                  });
                }}
              >
                Cancel editing
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="sp-card" style={{ marginTop: "1rem" }}>
        <h2>Your budgets</h2>

        {loading ? (
          <p>Loading budgets...</p>
        ) : budgets.length === 0 ? (
          <p>No budgets found yet.</p>
        ) : (
          budgets.map((budget) => (
            <article
              key={budget.id}
              style={{
                padding: "1rem 0",
                borderBottom: "1px solid var(--sp-border)",
              }}
            >
              <strong>{budget.name}</strong>
              <p>
                KES {Number(budget.amount).toLocaleString()} ·{" "}
                {budget.period ?? "monthly"}
              </p>

              <div className="sp-form__row">
                <button
                  className="sp-button"
                  type="button"
                  onClick={() => startEditing(budget)}
                >
                  Edit
                </button>
                <button
                  className="sp-button"
                  type="button"
                  onClick={() => handleDelete(budget.id)}
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        )}
      </section>
    </main>
  );
}