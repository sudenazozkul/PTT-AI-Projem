export const formatNumber = (value: number, digits = 0) =>
  new Intl.NumberFormat("tr-TR", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);

export const formatCurrency = (value: number) =>
  new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(value);

export const shortDate = (value: string) =>
  new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "short" }).format(
    new Date(value),
  );

export const monthDate = (value: string) =>
  new Intl.DateTimeFormat("tr-TR", { month: "short", year: "numeric" }).format(
    new Date(value),
  );

export const fullDate = (value: string) =>
  new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
