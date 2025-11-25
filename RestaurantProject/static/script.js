function addMenuItem() {
    const menuList = document.getElementById('menu-list');
    const newItem = document.createElement('li');
    newItem.textContent = 'New Menu Item';
    menuList.appendChild(newItem);
}