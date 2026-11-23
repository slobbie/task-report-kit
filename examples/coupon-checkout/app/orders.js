document.getElementById('list').innerHTML = ORDERS.map((o) =>
  `<div class="order" data-no="${o.no}"><div class="date">${o.date}</div><div class="date">Order ${o.no}</div><div class="title">${o.title}</div><div>Amount paid <b>${won(o.paid)}</b></div>${o.coupon ? `<div class="used">Coupon ${o.coupon} used (-${won(o.discount)})</div>` : ''}</div>`).join('');
