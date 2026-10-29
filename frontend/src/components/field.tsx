import type { UseFormRegisterReturn } from "react-hook-form";

import { enumLabel } from "@/lib/format";

// The form controls of the vanilla client, wired to react-hook-form. Each one labels its
// control, ties its hint and its error to it through aria-describedby, and marks it
// aria-invalid while the error shows (RS-71).

type FieldProps = {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  /** Spans both columns of a two-column form. */
  wide?: boolean;
  register: UseFormRegisterReturn;
};

const CONTROL =
  "mt-1.5 block min-h-11 w-full rounded-[7px] border border-input-line bg-input-bg px-3 py-2.5 text-sm text-ink aria-invalid:border-bad";

function described(id: string, hint?: string, error?: string): string | undefined {
  return [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
}

function controlProps({ id, hint, error, required, register }: FieldProps) {
  return {
    id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": described(id, hint, error),
    "aria-required": required || undefined,
    ...register,
  };
}

function Label({ id, label, required }: Pick<FieldProps, "id" | "label" | "required">) {
  return (
    <label htmlFor={id} className="block text-[13px] font-medium text-label">
      {label}
      {required && <span className="font-normal text-muted"> (required)</span>}
    </label>
  );
}

function Notes({ id, hint, error }: Pick<FieldProps, "id" | "hint" | "error">) {
  return (
    <>
      {hint && (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-xs text-bad">
          {error}
        </p>
      )}
    </>
  );
}

/**
 * A text input or, with `multiline`, a textarea. Numbers use `inputMode` and stay text:
 * the API parses and validates them (hard rule 7), and an empty field means unknown.
 */
export function TextField({
  multiline,
  inputMode,
  ...props
}: FieldProps & { multiline?: boolean; inputMode?: "numeric" | "decimal" }) {
  return (
    <div className={props.wide ? "sm:col-span-2" : undefined}>
      <Label {...props} />
      {multiline ? (
        <textarea rows={3} className={CONTROL} {...controlProps(props)} />
      ) : (
        <input inputMode={inputMode} className={CONTROL} {...controlProps(props)} />
      )}
      <Notes {...props} />
    </div>
  );
}

/** A number typed as text: `integer` asks for the numeric keypad, otherwise decimal. */
export function NumberField({ integer, ...props }: FieldProps & { integer?: boolean }) {
  return <TextField {...props} inputMode={integer ? "numeric" : "decimal"} />;
}

/**
 * A select over enum values, each labelled with enumLabel. A current value the list does
 * not name (a newer API) is kept as an option, so saving never swaps it silently (RS-58).
 */
export function SelectField({
  options,
  current,
  ...props
}: FieldProps & { options: readonly string[]; current?: string | null }) {
  const values = current && !options.includes(current) ? [...options, current] : options;
  return (
    <div className={props.wide ? "sm:col-span-2" : undefined}>
      <Label {...props} />
      <select className={CONTROL} {...controlProps(props)}>
        {values.map((value) => (
          <option key={value} value={value}>
            {enumLabel(value)}
          </option>
        ))}
      </select>
      <Notes {...props} />
    </div>
  );
}

/** A checkbox with its label beside it. */
export function CheckboxField(props: Omit<FieldProps, "required">) {
  const { id, label, wide } = props;
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <label htmlFor={id} className="flex min-h-11 items-center gap-2.5 text-sm text-ink-soft">
        <input
          type="checkbox"
          className="size-[18px] shrink-0 accent-accent"
          {...controlProps(props)}
        />
        {label}
      </label>
      <Notes {...props} />
    </div>
  );
}

/**
 * A select over named choices outside a form, where the value and the label differ (a
 * sector id and its name). The empty value is the placeholder.
 */
export function ChoiceField({
  id,
  label,
  placeholder,
  choices,
  value,
  onChange,
}: {
  id: string;
  label: string;
  placeholder: string;
  choices: readonly { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <Label id={id} label={label} />
      <select
        id={id}
        className={CONTROL}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{placeholder}</option>
        {choices.map((choice) => (
          <option key={choice.value} value={choice.value}>
            {choice.label}
          </option>
        ))}
      </select>
    </div>
  );
}
