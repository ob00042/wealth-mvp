export const number = (value: number | string) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value));
export const money = (value: number | string, currency: string) => new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value));
export const palette = ['#19384d', '#5285a3', '#c79d61', '#86a8ba', '#627381', '#d8c6a8'];
