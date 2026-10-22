document.addEventListener('DOMContentLoaded', () => {
    checkSession();
    if (document.getElementById('menu-grid')) {
        loadProducts();
    }
    if (document.getElementById('featured-grid')) {
        loadFeaturedProducts();
    }
});

async function checkSession() {
    try {
        const res = await fetch('/api/session');
        const data = await res.json();
        const authLink = document.getElementById('auth-link');
        if (authLink) {
            if (data.logged_in) {
                authLink.innerHTML = `<a href="#" onclick="logoutUser()">Logout (${data.name})</a>`;
            } else {
                authLink.innerHTML = `<a href="login.html">Login / Register</a>`;
            }
        }
    } catch (e) {
        console.error('Session check failed', e);
    }
}

async function logoutUser() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = 'index.html';
}

function showMessage(elementId, text, isError = false) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'block';
    el.textContent = text;
    el.className = isError ? 'alert alert-error' : 'alert alert-success';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

async function loadFeaturedProducts() {
    const grid = document.getElementById('featured-grid');
    const res = await fetch('/api/products');
    const products = await res.json();
    grid.innerHTML = products.slice(0, 3).map(item => `
        <article class="card">
            <img src="${item.image}" alt="${item.name}">
            <div class="card-body">
                <div>
                    <span class="badge">${item.category}</span>
                    <h3>${item.name}</h3>
                    <p>${item.description}</p>
                </div>
                <div>
                    <div class="price">৳${item.price}</div>
                    <a href="menu.html" class="btn">View Full Menu</a>
                </div>
            </div>
        </article>
    `).join('');
}

async function loadProducts() {
    const grid = document.getElementById('menu-grid');
    const res = await fetch('/api/products');
    const products = await res.json();
    
    grid.innerHTML = products.map(item => `
        <article class="card">
            <img src="${item.image}" alt="${item.name}">
            <div class="card-body">
                <div>
                    <span class="badge">${item.category}</span>
                    <h3>${item.name}</h3>
                    <p>${item.description}</p>
                </div>
                <div>
                    <div class="price">৳${item.price}</div>
                    <div class="card-actions">
                        <button class="btn" onclick="orderFood('${item.name.replace(/'/g, "\\'")}', ${item.price})">Order Now</button>
                        <button class="btn btn-secondary" onclick="populateEditForm(${item.id}, '${item.name.replace(/'/g, "\\'")}', '${item.description.replace(/'/g, "\\'")}', ${item.price}, '${item.category}')">Edit</button>
                        <button class="btn btn-danger" onclick="deleteProduct(${item.id})">Delete</button>
                    </div>
                </div>
            </div>
        </article>
    `).join('');
}

async function orderFood(itemName, price) {
    const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_name: itemName, price: price })
    });
    const data = await res.json();
    alert(data.message);
}

async function handleProductSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('product-id').value;
    const name = document.getElementById('food-name').value.trim();
    const description = document.getElementById('food-desc').value.trim();
    const price = document.getElementById('food-price').value;
    const category = document.getElementById('food-category').value;
    const image = document.getElementById('food-image').value.trim();

    if (!name || !description || price <= 0) {
        showMessage('crud-msg', 'Please enter valid food name, description, and positive price!', true);
        return;
    }

    const payload = { name, description, price, category, image };
    const url = id ? `/api/products/${id}` : '/api/products';
    const method = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
        showMessage('crud-msg', data.message, false);
        document.getElementById('product-form').reset();
        document.getElementById('product-id').value = '';
        document.getElementById('form-submit-btn').textContent = 'Add Food Item';
        loadProducts();
    } else {
        showMessage('crud-msg', data.error, true);
    }
}

function populateEditForm(id, name, desc, price, category) {
    document.getElementById('product-id').value = id;
    document.getElementById('food-name').value = name;
    document.getElementById('food-desc').value = desc;
    document.getElementById('food-price').value = price;
    document.getElementById('food-category').value = category;
    document.getElementById('form-submit-btn').textContent = 'Update Food Item';
    document.getElementById('product-form').scrollIntoView({ behavior: 'smooth' });
}

async function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this food item?')) return;
    const res = await fetch(`/api/products/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadProducts();
    }
}

async function handleContactSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('contact-name').value.trim();
    const email = document.getElementById('contact-email').value.trim();
    const message = document.getElementById('contact-message').value.trim();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (name.length < 2) {
        showMessage('contact-msg', 'Please enter a valid name (at least 2 characters).', true);
        return;
    }
    if (!emailRegex.test(email)) {
        showMessage('contact-msg', 'Please enter a valid email address.', true);
        return;
    }
    if (message.length < 10) {
        showMessage('contact-msg', 'Message must be at least 10 characters long.', true);
        return;
    }

    const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, message })
    });
    const data = await res.json();
    if (res.ok) {
        showMessage('contact-msg', data.message, false);
        document.getElementById('contact-form').reset();
    } else {
        showMessage('contact-msg', data.error, true);
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (name.length < 3) {
        showMessage('reg-msg', 'Name must be at least 3 characters long.', true);
        return;
    }
    if (!emailRegex.test(email)) {
        showMessage('reg-msg', 'Invalid email address.', true);
        return;
    }
    if (password.length < 6) {
        showMessage('reg-msg', 'Password must be at least 6 characters long.', true);
        return;
    }

    const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (res.ok) {
        showMessage('reg-msg', data.message, false);
        document.getElementById('register-form').reset();
    } else {
        showMessage('reg-msg', data.error, true);
    }
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    if (!email || !password) {
        showMessage('login-msg', 'Please enter both email and password.', true);
        return;
    }

    const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok) {
        showMessage('login-msg', 'Login successful! Redirecting...', false);
        setTimeout(() => { window.location.href = 'menu.html'; }, 1000);
    } else {
        showMessage('login-msg', data.error, true);
    }
}
