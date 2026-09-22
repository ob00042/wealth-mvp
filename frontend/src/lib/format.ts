export const number = (value: number | string) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value));
export const money = (value: number | string, currency: string) => new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value));
export const palette = ['#244e61', '#80a7a5', '#4266a2', '#c48b61', '#acc3d7', '#667664'];
