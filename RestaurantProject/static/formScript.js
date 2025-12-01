let itemCount = 1;

function addItem() {
  itemCount++;

  const container = document.getElementById("items-container");

  const div = document.createElement("div");
  div.classList.add("item-row");

  div.innerHTML = `
    <h4>Item ${itemCount}</h4>

    <label>Item Name</label>
    <input type="text" name="item_name[]" required>

    <label>Price</label>
    <input type="number" name="item_price[]" step="0.01" min="0" required>

    <label>Category</label>
    <select name="item_category[]" required>
      <option value="">-- Select category --</option>
      <option value="Appetizer">Appetizer</option>
      <option value="Entree">Entree</option>
      <option value="Dessert">Dessert</option>
      <option value="Drinks">Drinks</option>
    </select>

    <label>Description</label>
    <textarea name="item_description[]" rows="2"></textarea>
  `;

  container.appendChild(div);
}