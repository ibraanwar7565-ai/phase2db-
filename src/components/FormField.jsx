import React from "react";

export default function FormField({
  id,
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  required = false,
  helpText,
  error,
  options = [],
  as = "input",
  min,
  max,
  step,
}) {
  const describedBy = [
    helpText ? `${id}-help` : null,
    error ? `${id}-error` : null,
  ]
    .filter(Boolean)
    .join(" ") || undefined;

  const commonProps = {
    id,
    name: id,
    value,
    onChange,
    required,
    placeholder,
    min,
    max,
    step,
    "aria-invalid": Boolean(error),
    "aria-describedby": describedBy,
    className:
      as === "select"
        ? "sp-select"
        : as === "textarea"
          ? "sp-textarea"
          : "sp-input",
  };

  return (
    <div className="sp-field">
      <label className="sp-label" htmlFor={id}>
        {label}{required ? " *" : ""}
      </label>

      {as === "select" ? (
        <select {...commonProps}>
          <option value="">Select {label.toLowerCase()}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : as === "textarea" ? (
        <textarea {...commonProps} />
      ) : (
        <input {...commonProps} type={type} />
      )}

      {helpText && (
        <small className="sp-help" id={`${id}-help`}>
          {helpText}
        </small>
      )}

      {error && (
        <small className="sp-error" id={`${id}-error`}>
          {error}
        </small>
      )}
    </div>
  );
}