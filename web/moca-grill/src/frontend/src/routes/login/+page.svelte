<script>

    let username = "", password = "";

    const handleLogin = async (e) => {
        e.preventDefault();

        const data = {
            login: username,
            password: password,
        };

        const response = await fetch('/accounts/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        let response_data =  await response.json();

        if (response.ok) {
            localStorage.setItem('token', response_data.token);
            window.location.href = '/';
        } else {
            alert(response_data.detail);
        }
    };
</script>

<div class="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
    <h2 class="text-2xl font-bold mb-6 text-center">Login</h2>
    <form action="/register" method="POST">
        <div class="mb-4">
            <label class="block text-gray-700" for="username">Username</label>
            <input
                type="text"
                id="username"
                name="username"
                bind:value={username}
                class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-bg-secondary"
                required
            />
        </div>
        <div class="mb-4">
            <label class="block text-gray-700" for="password">Password</label>
            <input
                type="password"
                id="password"
                name="password"
                bind:value={password}
                class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-bg-secondary"
                required
            />
        </div>
        <button
            type="submit"
            class="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary"
            on:click|preventDefault={handleLogin}
            >Login</button
        >
    </form>
    <p class="text-center text-gray-600 mt-4">
        Don't have an account? <a
            href="/register"
            class="text-bg-secondary hover:underline">Register</a
        >
    </p>
</div>
