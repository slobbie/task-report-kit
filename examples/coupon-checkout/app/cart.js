let applied = COUPON;

function render() {
  document.getElementById('items').innerHTML = CART.map((i) =>
    `<div class="item"><div><div class="name">${i.name}</div><div class="opt">${i.opt}</div></div><div>${won(i.price * i.qty)}</div></div>`).join('');
  document.getElementById('coupon').innerHTML = applied
    ? `<div><div class="cname">${applied.name}</div><div class="cexp">${applied.label}</div></div><span>Applied</span>`
    : `<div><div class="cname" style="color:#8b929c">No coupon applied</div></div>`;
  document.getElementById('sub').textContent = won(subtotal());
  document.getElementById('dis').textContent = discountOf(applied) ? '-' + won(discountOf(applied)) : won(0);
  document.getElementById('total').textContent = won(subtotal() - discountOf(applied));
}

document.getElementById('pay').addEventListener('click', () => {
  // Re-check the coupon expiry right before payment (stands in for the server check in this demo)
  if (applied && NOW > applied.expiresAt) {
    applied = null;
    document.getElementById('notice').innerHTML =
      '<div class="notice">This coupon has expired. Check the total without the discount and place your order again.</div>';
    render();
    return;
  }
  location.href = 'complete.html';
});

render();
