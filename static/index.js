import { apiFetch, clearToken, onAuthChange, setToken } from './auth.js';

export const perPage = 20;
export const currentPage = {
	products: 1,
	users: 1,
	orders: 1,
};
const productFilter = { name: '', min: '', max: '' };
const userFilter = { name: '', email: '' };
const orderFilter = { user: '' };

let productFilterTimer = null;
let userFilterTimer = null;
let orderFilterTimer = null;

function buildQS(base, params) {
	const qs = new URLSearchParams(base);
	for (const [k, v] of Object.entries(params)) {
		if (v !== '' && v !== null && v !== undefined) qs.append(k, v);
	}
	return qs;
}

/** Show a coloured toast.  type = “danger” | “success” | “info” | “warning” */
function showToast(message, type = 'info') {
	const el = document.getElementById('mainToast');

	// Switch colour (remove old bg-* classes first)
	el.classList.remove('bg-danger', 'bg-success', 'bg-info', 'bg-warning');
	el.classList.add(`bg-${type}`);

	// Set the message text
	el.querySelector('.toast-body').textContent = message;

	// Show it
	bootstrap.Toast.getOrCreateInstance(el).show();
}

function showLoading() {
	document.getElementById('contentArea').innerHTML = `
                <div class="d-flex justify-content-center py-5">
                <div class="spinner-border" role="status" aria-label="Loading"></div>
                </div>`;
}

const templates = {
	product: /*html*/ `
    <div class="mb-3">
        <label class="form-label">Name</label>
        <input name="name" class="form-control" required>
    </div>
    <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea name="description" class="form-control"></textarea>
    </div>
    <div class="row g-3">
        <div class="col">
        <label class="form-label">Price</label>
        <input name="price" type="number" step="0.01" min="0" class="form-control" required>
        </div>
        <div class="col">
        <label class="form-label">Stock</label>
        <input name="stock" type="number" min="0" class="form-control" required>
        </div>
    </div>`,
};

templates.user = /*html*/ `
<div class="mb-3">
    <label class="form-label">Username</label>
    <input name="username" class="form-control" required>
</div>
<div class="mb-3">
    <label class="form-label">Email</label>
    <input name="email" type="email" class="form-control" required>
</div>
<div class="mb-3">
    <label class="form-label">Password</label>
    <input name="password" type="password" class="form-control" required minlength="6">
</div>`;

templates.order = /*html*/ `
<div class="mb-3">
    <label class="form-label">User&nbsp;ID</label>
    <input name="user_id" type="number" min="1" class="form-control" required>
</div>
<div class="mb-3">
    <label class="form-label">Total&nbsp;price</label>
    <input name="total_price" type="number" step="0.01" min="0" class="form-control" required>
</div>`;

const addConfig = {
	products: { label: '➕ Add product', open: openProductForm },
	users: { label: '➕ Add user', open: openUserForm },
	orders: { label: '➕ Add order', open: openOrderForm },
};

const editModal = new bootstrap.Modal('#editModal');
const modalForm = document.getElementById('modalForm');
const modalBody = document.getElementById('modalBody');
const modalTitle = document.getElementById('modalTitle');

let activePage = 'products';

function openProductForm() {
	modalTitle.textContent = 'Add product';
	modalBody.innerHTML = templates.product;
	modalForm.onsubmit = submitNewProduct; // wire the handler
	editModal.show();
}

function openUserForm() {
	modalTitle.textContent = 'Add user';
	modalBody.innerHTML = templates.user;
	modalForm.onsubmit = submitNewUser;
	editModal.show();
}

function openOrderForm() {
	modalTitle.textContent = 'Add order';
	modalBody.innerHTML = templates.order;
	modalForm.onsubmit = submitNewOrder;
	editModal.show();
}

function openEditProductForm(id, currentPrice, currentStock) {
	modalTitle.textContent = 'Edit product';

	modalBody.innerHTML = /*html*/ `
	<div class="mb-3">
		<label class="form-label">Price</label>
		<input name="price" type="number" step="0.01" min="0"
			class="form-control" value="${currentPrice}" required>
	</div>
	<div class="mb-3">
		<label class="form-label">Stock</label>
		<input name="stock" type="number" min="0"
			class="form-control" value="${currentStock}" required>
	</div>`;

	modalForm.onsubmit = (e) => submitEditedProduct(e, id, Number(currentPrice), Number(currentStock));
	editModal.show();
}

function openEditUserForm(id, currentUsername, currentEmail) {
	modalTitle.textContent = 'Edit user';
	modalBody.innerHTML = /*html*/ `
	<div class="mb-3">
		<label class="form-label">Username</label>
		<input name="username" class="form-control" value="${currentUsername}" required>
	</div>
	<div class="mb-3">
		<label class="form-label">Email</label>
		<input name="email" type="email" class="form-control" value="${currentEmail}" required>
	</div>
		<div class="mb-3">
		<label class="form-label">Password</label>
		<input type="password" class="form-control" placeholder="(not editable here)" disabled>
		<div class="form-text">
			Use the “Forgot password?” flow to change it.
		</div>
		</div>`;

	modalForm.onsubmit = (e) => submitEditedUser(e, id, currentUsername, currentEmail);
	editModal.show();
}

function openEditOrderForm(id, currentTotal) {
	modalTitle.textContent = 'Edit order';
	modalBody.innerHTML = /*html*/ `
	<div class="mb-3">
		<label class="form-label">Total price</label>
		<input name="total_price"
			type="number" step="0.01" min="0" class="form-control" value="${currentTotal}" required>
	</div>`;
	modalForm.onsubmit = (e) => submitEditedOrder(e, id, currentTotal);
	editModal.show();
}

async function submitEditedProduct(e, id, oldPrice, oldStock) {
	e.preventDefault();
	const raw = Object.fromEntries(new FormData(modalForm));

	// convert → numbers; blank means “unchanged”
	const patch = {}; // empty ⇢ nothing will be sent

	if (raw.price !== '' && Number(raw.price) !== oldPrice) patch.price = Number(raw.price);
	if (raw.stock !== '' && Number(raw.stock) !== oldStock) patch.stock = Number(raw.stock);

	if (Object.keys(patch).length === 0) {
		// nothing changed?
		showToast('Nothing to update', 'info');
		return;
	}
	try {
		await apiFetch(`/products/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(patch),
		});

		showToast('Product updated', 'success');
		editModal.hide();
		loadProducts(currentPage.products ?? 1); // stay on same page
	} catch (err) {
		showToast(`Failed: ${err.message}`, 'danger');
	}
}

async function submitEditedUser(e, id, oldUsername, oldEmail) {
	e.preventDefault();
	const raw = Object.fromEntries(new FormData(modalForm));

	const patch = {};
	if (raw.username && raw.username !== oldUsername) patch.username = raw.username.trim();
	if (raw.email && raw.email !== oldEmail) patch.email = raw.email.trim();

	if (Object.keys(patch).length === 0) {
		showToast('Nothing to update', 'info');
		return;
	}

	try {
		await apiFetch(`/users/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(patch),
		});
		showToast('User updated', 'success');
		editModal.hide();
		loadUsers(currentPage.users ?? 1); // stay on current page
	} catch (err) {
		showToast(`Failed: ${err.message}`, 'danger');
	}
}

async function submitEditedOrder(e, id, oldTotal) {
	e.preventDefault();
	const raw = Object.fromEntries(new FormData(modalForm));

	const patch = {};
	if (raw.total_price !== '' && Number(raw.total_price) !== Number(oldTotal)) {
		patch.total_price = Number(raw.total_price);
	}

	if (Object.keys(patch).length === 0) {
		showToast('Nothing to update', 'info');
		return;
	}

	try {
		await apiFetch(`/orders/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(patch),
		});
		showToast('Order updated', 'success');
		editModal.hide();
		loadOrders(currentPage.orders ?? 1); // stay on same page
	} catch (err) {
		showToast(`Failed: ${err.message}`, 'danger');
	}
}

async function submitNewProduct(e) {
	e.preventDefault(); // keep the page from reloading

	const data = Object.fromEntries(new FormData(modalForm));
	// convert numeric fields (FormData gives you strings):
	data.price = Number(data.price);
	data.stock = Number(data.stock);

	try {
		await apiFetch('/products', {
			method: 'POST',
			body: JSON.stringify(data),
		});

		showToast('Product created', 'success');
		editModal.hide();
		loadProducts(1); // refresh first page so the new row is visible
	} catch (err) {
		showToast(`Failed: ${err.message}`, 'danger');
	}
}

async function submitNewUser(e) {
	e.preventDefault();
	const data = Object.fromEntries(new FormData(modalForm));

	try {
		await apiFetch('/users', {
			method: 'POST',
			body: JSON.stringify(data),
		});

		showToast('User created', 'success');
		editModal.hide();
		loadUsers(1); // reload first page of Users
	} catch (err) {
		showToast(`Failed: ${err.message}`, 'danger');
	}
}

async function submitNewOrder(e) {
	e.preventDefault();
	const data = Object.fromEntries(new FormData(modalForm));
	data.user_id = Number(data.user_id);
	data.total_price = Number(data.total_price);

	try {
		await apiFetch('/orders', { method: 'POST', body: JSON.stringify(data) });
		showToast('Order created', 'success');
		editModal.hide();
		loadOrders(1);
	} catch (err) {
		showToast(`Failed: ${err.message}`, 'danger');
	}
}

function setActiveTab(page) {
	activePage = page;

	for (const a of document.querySelectorAll('#mainTabs .nav-link')) {
		a.classList.toggle('active', a.dataset.page === page);
	}

	const conf = addConfig[page];
	if (conf) {
		addBtn.textContent = conf.label;
		addBtn.classList.remove('d-none');
	} else {
		addBtn.classList.add('d-none');
	}

	document.getElementById('productFilter').classList.toggle('d-none', page !== 'products');
	document.getElementById('userFilter').classList.toggle('d-none', page !== 'users');
	document.getElementById('orderFilter').classList.toggle('d-none', page !== 'orders');
}

// swap between login form and main UI
onAuthChange((isLoggedIn) => {
	document.getElementById('loginForm').style.display = isLoggedIn ? 'none' : 'block';
	document.getElementById('mainContent').style.display = isLoggedIn ? 'block' : 'none';

	document.getElementById('btnLogout').classList.toggle('d-none', !isLoggedIn);
	addBtn.classList.toggle('d-none', !isLoggedIn);

	if (isLoggedIn) {
		// fresh session → always start on Products
		setActiveTab('products');
		showLoading();
		loadProducts();
	} else {
		// leaving → clear any leftover highlight
		setActiveTab(null);
		Object.assign(productFilter, { name: '', min: '', max: '' });
		for (const id of ['fName', 'fMin', 'fMax']) document.getElementById(id).value = '';

		Object.assign(userFilter, { name: '', email: '' });
		for (const id of ['uName', 'uEmail']) document.getElementById(id).value = '';

		orderFilter.user = '';
		document.getElementById('oUser').value = '';
	}
});

// wire up your login form:
document.getElementById('loginForm').addEventListener('submit', async (e) => {
	e.preventDefault();
	const u = e.target.username.value;
	const p = e.target.password.value;
	const msg = document.getElementById('loginError');
	msg.textContent = '';

	try {
		const res = await fetch('/login', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ username: u, password: p }),
		});
		if (!res.ok) throw new Error('Login failed');
		const { token } = await res.json();
		setToken(token);
	} catch (err) {
		// show an inline error message instead of alert()
		msg.textContent = err.message;
	}
});

document.getElementById('mainTabs').addEventListener('click', (e) => {
	const link = e.target.closest('[data-page]');
	if (!link) return;
	e.preventDefault();

	const page = link.dataset.page; // 'products' | 'users' | 'orders'
	setActiveTab(page); // highlight the tab
	showLoading();

	// call the matching loader
	({ products: loadProducts, users: loadUsers, orders: loadOrders })[page](currentPage[page] ?? 1);
});

// hook up logout button
document.getElementById('btnLogout').addEventListener('click', () => {
	clearToken();
});

export function renderPagination(resource, page, count) {
	const totalPages = Math.ceil(count / perPage) || 1;
	let html = '<nav><ul class="pagination">';
	for (let i = 1; i <= totalPages; i++) {
		html += `
        <li class="page-item ${i === page ? 'active' : ''}">
        <a href="#" class="page-link" data-resource="${resource}" data-page="${i}">${i}</a>
        </li>`;
	}
	html += '</ul></nav>';
	document.getElementById('contentArea').insertAdjacentHTML('beforeend', html);
}

export function renderTable(fields, rows, renderActions) {
	const target = document.getElementById('contentArea');

	if (!rows?.length) {
		target.innerHTML = `<p class="text-muted">No records.</p>`;
		return;
	}

	const thead = `<tr>${fields.map((f) => `<th>${f}</th>`).join('')}<th>Actions</th></tr>`;

	const tbody = rows
		.map((r) => {
			const dataCells = fields.map((f) => `<td>${r[f]}</td>`).join('');

			const actions = renderActions ? `<td>${renderActions(r)}</td>` : '<td></td>';
			return `<tr>${dataCells}${actions}</tr>`;
		})
		.join('');

	target.innerHTML = `
        <table class="table table-striped">
            <thead>${thead}</thead>
            <tbody>${tbody}</tbody>
        </table>
        `;
}

export async function deleteProduct(id) {
	if (!confirm(`Delete product ${id}?`)) return;

	try {
		await apiFetch(`/products/${id}`, { method: 'DELETE' });

		loadProducts(currentPage.products);
	} catch (err) {
		showToast(`Failed to delete product: ${err.message}`, 'danger');
	}
}

window.deleteProduct = deleteProduct;
window.editProduct = openEditProductForm;
window.deleteUser = deleteUser;
window.editUser = openEditUserForm;
window.deleteOrder = deleteOrder;
window.editOrder = openEditOrderForm;

export async function deleteUser(id) {
	if (!confirm(`Delete user ${id}?`)) return;

	try {
		await apiFetch(`/users/${id}`, { method: 'DELETE' });

		loadUsers(currentPage.users);
	} catch (err) {
		showToast(`Failed to delete user: ${err.message}`, 'danger');
	}
}

export async function deleteOrder(id) {
	if (!confirm(`Delete order ${id}?`)) return;

	try {
		await apiFetch(`/orders/${id}`, { method: 'DELETE' });

		loadOrders(currentPage.orders);
	} catch (err) {
		showToast(`Failed to delete order: ${err.message}`, 'danger');
	}
}

// Loaders for each resource
async function loadProducts(page = 1) {
	showLoading();

	currentPage.products = page;

	const qs = buildQS(`page=${page}&per_page=${perPage}`, {
		name_contains: productFilter.name,
		min_price: productFilter.min,
		max_price: productFilter.max,
	});

	const { items, total } = await apiFetch(`/products?${qs.toString()}`);

	renderTable(
		['id', 'name', 'price', 'stock'],
		items,
		(product) => `
		<button class="btn btn-sm btn-outline-secondary me-1"
			onclick="editProduct(${product.id}, ${product.price}, ${product.stock})">Edit</button>

		<button class="btn btn-sm btn-outline-danger" onclick="deleteProduct(${product.id})">Delete</button>`,
	);

	renderPagination('products', page, total);
}

async function loadUsers(page = 1) {
	showLoading();

	currentPage.users = page;

	const qs = buildQS(
		{ page, per_page: 20 },
		{
			username_contains: userFilter.name,
			email_contains: userFilter.email,
		},
	);

	const { items, total } = await apiFetch(`/users?${qs}`);

	renderTable(
		['id', 'username', 'email'],
		items,
		(user) => `
		<button class="btn btn-sm btn-outline-secondary me-1" 
			onclick="editUser(${user.id}, '${user.username}', '${user.email}')">Edit</button>

		<button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">Delete</button>`,
	);

	renderPagination('users', page, total);
}

async function loadOrders(page = 1) {
	showLoading();

	currentPage.orders = page;

	const qs = buildQS({ page, per_page: 20 }, { user_id: orderFilter.user || undefined });

	const { items, total } = await apiFetch(`/orders?${qs}`);

	renderTable(
		['id', 'user_id', 'total_price', 'created_at'],
		items,
		(order) => `
		<button class="btn btn-sm btn-outline-secondary me-1" onclick="editOrder(${order.id}, ${order.total_price})">Edit</button>
		<button class="btn btn-sm btn-outline-danger" onclick="deleteOrder(${order.id})">Delete</button>`,
	);

	renderPagination('orders', page, total);
}

const addBtn = document.getElementById('btnAdd');
addBtn.addEventListener('click', () => {
	const conf = addConfig[activePage];
	if (conf) conf.open();
});

for (const id of ['fName', 'fMin', 'fMax']) {
	const el = document.getElementById(id);

	// live typing — debounced
	el.addEventListener('input', (e) => {
		updateFilter(id, e.target.value);
		clearTimeout(productFilterTimer);
		productFilterTimer = setTimeout(() => loadProducts(1), 500);
	});

	// leaving the field — immediate
	el.addEventListener('blur', (e) => {
		updateFilter(id, e.target.value);
		clearTimeout(productFilterTimer);
		loadProducts(1);
	});
}

for (const [id, key] of [
	['uName', 'name'],
	['uEmail', 'email'],
]) {
	const el = document.getElementById(id);

	el.addEventListener('input', (e) => {
		userFilter[key] = e.target.value.trim();
		clearTimeout(userFilterTimer);
		userFilterTimer = setTimeout(() => loadUsers(1), 500);
	});

	el.addEventListener('blur', (e) => {
		userFilter[key] = e.target.value.trim();
		clearTimeout(userFilterTimer);
		loadUsers(1);
	});
}

{
	const el = document.getElementById('oUser');

	el.addEventListener('input', (e) => {
		orderFilter.user = e.target.value.trim();
		clearTimeout(orderFilterTimer);
		orderFilterTimer = setTimeout(() => loadOrders(1), 500);
	});

	el.addEventListener('blur', (e) => {
		orderFilter.user = e.target.value.trim();
		clearTimeout(orderFilterTimer);
		loadOrders(1);
	});
}

function updateFilter(id, val) {
	if (id === 'fName') productFilter.name = val.trim();
	if (id === 'fMin') productFilter.min = val;
	if (id === 'fMax') productFilter.max = val;
}

document.addEventListener('click', (e) => {
	const link = e.target.closest('.page-link');
	if (!link) return;
	e.preventDefault();
	const res = link.dataset.resource;
	const pg = Number.parseInt(link.dataset.page, 20);
	currentPage[res] = pg;
	({ products: loadProducts, users: loadUsers, orders: loadOrders })[res](pg);
});
