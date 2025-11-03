// Load cart from localStorage
let cart = JSON.parse(localStorage.getItem("cart") || "[]");

// Add to Cart button
document.querySelectorAll(".add-to-cart").forEach(btn => {
  btn.addEventListener("click", (e) => {
    const card = e.target.closest(".product-card");
    const name = card.querySelector("h3").innerText;
    const priceText = card.querySelector(".price").innerText.replace(/₹|,/g, '');
    const price = parseFloat(priceText);

    const existing = cart.find(item => item.name === name);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({ name, qty: 1, price });
    }

    localStorage.setItem("cart", JSON.stringify(cart));
    alert(`${name} added to cart!`);
  });
});
