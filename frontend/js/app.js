
const form = document.querySelector("#product-form");
const list = document.querySelector("#products");
const message = document.querySelector("#message");

async function loadProducts() {
  message.textContent = "Loading products...";

  try {
    const response = await fetch("/api/products");
    if (!response.ok) throw new Error("Could not load products");

    const products = await response.json();
    list.replaceChildren();

    products.forEach((product) => {
      const item = document.createElement("li");
      item.textContent =
        `${product.name} — ₹${Number(product.price).toFixed(2)}`;
      list.appendChild(item);
    });

    message.textContent = `${products.length} product(s) loaded.`;
  } catch (error) {
    message.textContent = error.message;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "Saving product...";

  const payload = {
    name: form.elements.name.value.trim(),
    price: Number(form.elements.price.value)
  };

  try {
    const response = await fetch("/api/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Could not save product");
    }

    form.reset();
    message.textContent = "Product saved successfully.";
    await loadProducts();
  } catch (error) {
    message.textContent = error.message;
  }
});

document.querySelector("#refresh")
  .addEventListener("click", loadProducts);

loadProducts();
