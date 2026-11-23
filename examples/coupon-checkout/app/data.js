// Demo data. "Now" is fixed just after the coupon expired.
const NOW = new Date('2026-11-23T00:10:00+09:00');
const CART = [
  { name: 'Wireless Earbuds Case', opt: 'Color: Mint', price: 19.0, qty: 1 },
  { name: 'USB-C Charging Cable (1 m)', opt: 'Qty: 2', price: 9.0, qty: 2 },
];
const COUPON = { name: 'WELCOME10 (10% off)', rate: 0.1, expiresAt: new Date('2026-11-22T23:59:00+09:00'), label: 'Valid until Nov 22, 11:59 PM' };
const ORDERS = [
  { no: '20261123-0012', date: 'Nov 23, 2026, 12:08 AM', title: 'Wireless Earbuds Case and 1 more', paid: 33.3, coupon: 'WELCOME10', discount: 3.7 },
  { no: '20261102-0441', date: 'Nov 2, 2026, 2:21 PM', title: 'Laptop Stand', paid: 27.0 },
];
const won = (n) => '$' + n.toFixed(2);
const subtotal = () => CART.reduce((s, i) => s + i.price * i.qty, 0);
const discountOf = (c) => (c ? Math.round(subtotal() * c.rate * 100) / 100 : 0);
