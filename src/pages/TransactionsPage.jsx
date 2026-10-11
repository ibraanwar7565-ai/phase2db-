import React, { useState } from "react";
import FormField from "../components/FormField";
import "../styles/theme.css";

export default function TransactionsPage({ onSave }) {
  const [form, setForm] = useState({
    description: "",
    amount: "",
    type: "expense",
    category: "",
    date: new Date().toISOString().slice(0, 10),
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
      !form.description.trim() ||
      !form.amount ||
      Number(form.amount) <= 0 ||
      !form.date
    ) {
      setMessage("Complete the required fields and enter a valid amount.");
      return;
    }

    try {
      if (onSave) {
        await onSave({
          ...form,
          amount: Number(form.amount),
        });
      }

      setMessage("Transaction submitted successfully.");
    } catch {
      setMessage("Could not save the transaction. Please try again.");
    }
  }

  return (
    <main className="sp-page">
      <header className="sp-page__header">
        <p className="sp-page__eyebrow">SmartPesa</p>
        <h1 className="sp-page__title">Add a transaction</h1>
        <p className="sp-page__description">
          Record your income and expenses.
        </p>
      </header>

      <section className="sp-card">
        <form className="sp-form" onSubmit={handleSubmit}>
          <FormField
            id="transaction-description"
            label="Description"
            value={form.description}
            onChange={updateField("description")}
            placeholder="e.g. Shopping"
            required
          />

          <div className="sp-form__row">
            <FormField
              id="transaction-amount"
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
              id="transaction-type"
              label="Transaction type"
              as="select"
              value={form.type}
              onChange={updateField("type")}
              options={[
                { value: "expense", label: "Expense" },
                { value: "income", label: "Income" },
              ]}
              required
            />
          </div>

          <div className="sp-form__row">
            <FormField
              id="transaction-category"
              label="Category"
              value={form.category}
              onChange={updateField("category")}
              placeholder="e.g. Food"
            />

            <FormField
              id="transaction-date"
              label="Date"
              type="date"
              value={form.date}
              onChange={updateField("date")}
              required
            />
          </div>

          {message && (
            <p className="sp-alert" role="status">
              {message}
            </p>
          )}

          <button className="sp-button" type="submit">
            Save transaction
          </button>
        </form>
      </section>
    </main>
  );
}