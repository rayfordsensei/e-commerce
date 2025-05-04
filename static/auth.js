const STORAGE_KEY = 'jwt';
export let jwtToken = localStorage.getItem(STORAGE_KEY);
setTimeout(() => _notify());

// —— Subscribe/unsubscribe UI callbacks for login state changes —— //
const _subs = new Set();
export function onAuthChange(fn) {
	_subs.add(fn);
	return () => _subs.delete(fn);
}
function _notify() {
	for (const fn of _subs) {
		fn(!!jwtToken);
	}
}

// —— Call this after you get a token from /login —— //
export function setToken(token) {
	jwtToken = token;
	localStorage.setItem(STORAGE_KEY, token);
	_notify();

	// if your JWT has a numeric "exp" field, auto-logout when it expires:
	try {
		const payload = JSON.parse(atob(token.split('.')[1]));
		if (payload.exp) {
			const ms = payload.exp * 1000 - Date.now() - 30_000; // 30s early
			if (ms > 0)
				setTimeout(() => {
					clearToken();
				}, ms);
		}
	} catch (e) {
		/* ignore if no exp */
	}
}

// —— Remove the token & let subscribers know —— //
export function clearToken() {
	jwtToken = '';
	localStorage.removeItem(STORAGE_KEY);
	_notify();
}

// —— A thin wrapper around fetch that auto-injects the JWT and retries ONCE on 401 —— //
export async function apiFetch(path, opts = {}) {
	const headers = new Headers(opts.headers || {});
	if (jwtToken) headers.set('Authorization', `Bearer ${jwtToken}`);
	headers.set('Content-Type', 'application/json');

	const url = `${window.API_BASE}${path}`
	const res = await fetch(url, {
		...opts,
		headers,
		credentials: 'include', // if you ever do cookies later
		mode: 'cors',
	});

	if (res.status === 401) {
		clearToken();
		// re-show login UI (you’ll wire this up below)
		location.reload();
	}

	if (res.status === 204) return null;

	// parse JSON and include X-Total-Count header if present
	const data = await res.json();

	if (Array.isArray(data)) {
		const totalHeader = res.headers.get('X-Total-Count');
		return {
			items: data,
			total: totalHeader != null ? Number(totalHeader) : data.length,
		};
	}
	return data;
}

window.addEventListener('storage', (e) => {
	if (e.key !== STORAGE_KEY) return;
	jwtToken = e.newValue || '';
	_notify();
});
