import React, { useState } from "react";
import FormField from "../components/FormField";
import "../styles/theme.css";

export default function BudgetPage({ onSave }) {
  const [form, setForm] = useState({
    name: "",
    amount: "",
    period: "monthly",
    category: "",
  });

  const [message, setMessage] = useState("");

  const updateField = (field) => (event) => {
    setForm((previous) => ({
      ...previous,
      [field]: event.target.value,
    }));
  };

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");

    if (
      !form.name.trim() ||
      !form.amount ||
      Number(form.amount) <= 0
    ) {
      setMessage("Enter a budget name and a valid amount.");
      return;
    }

    try {
      if (onSave) {
        await onSave({
          ...form,
          amount: Number(form.amount),
        });
      }

      setMessage("Budget submitted successfully.");
    } catch {
      setMessage("Could not save the budget. Please try again.");
    }
  }

  return (
    <main className="sp-page">
      <header className="sp-page__header">
        <p className="sp-page__eyebrow">SmartPesa</p>
        <h1 className="sp-page__title">Create a budget</h1>
        <p className="sp-page__description">
          Set a spending limit and manage your money.
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
              placeholder="0.00"
              min="0.01"
              step="0.01"
              required
            />

            <FormField
              id="budget-period"
              label="Budget period"
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
            placeholder="e.g. Food or transport"
          />

          {message && (
            <p className="sp-alert" role="status">
              {message}
            </p>
          )}

          <button className="sp-button" type="submit">
            Save budget
          </button>
        </form>
      </section>
    </main>
  );
}