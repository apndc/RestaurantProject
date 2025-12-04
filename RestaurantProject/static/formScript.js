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
    <br><br>

    <label>Price</label>
    <input type="number" name="item_price[]" step="0.01" min="0" required>
    <br><br>    

    <label>Category</label>
    <select name="item_category[]" required>
        <option value="">-- Select category --</option>
        <option value="Appetizer">Appetizer</option>
        <option value="Entree">Entree</option>
        <option value="Dessert">Dessert</option>
        <option value="Drinks">Drinks</option>
    </select>
    <br><br> 

    <label>Description</label><br>
    <textarea name="item_description[]" class="Descriptions" rows="2"></textarea>
    <br><br> 
  `;

  container.appendChild(div);
}

function removeItem() {
  const container = document.getElementById("items-container");
  const items = container.getElementsByClassName("item-row");

  // Prevent deleting the very first item
  if (items.length > 1) {
    container.removeChild(items[items.length - 1]);
    itemCount--;
  } else {
    alert("At least one item is required.");
  }
}