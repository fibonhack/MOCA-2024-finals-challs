<script>
    let username = "",
        password = "",
        password_confirm = "";

    const handleRegister = async (e) => {
        const data = {
            username: username,
            password: password,
            password_confirm: password_confirm,
        };

        const response = await fetch("/accounts/register/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            window.location.href = "/login";
        } else {
            alert("Invalid credentials");
        }
    };
</script>

<div class="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
    <h2 class="text-2xl font-bold mb-6 text-center">Create an Account</h2>
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
        <div class="mb-4">
            <label class="block text-gray-700" for="confirm-password"
                >Confirm Password</label
            >
            <input
                type="password"
                id="confirm-password"
                name="confirm_password"
                bind:value={password_confirm}
                class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-bg-secondary"
                required
            />
        </div>
        <button
            type="submit"
            class="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary"
            on:click|preventDefault={handleRegister}>Register</button
        >
    </form>
    <p class="text-center text-gray-600 mt-4">
        Already have an account? <a
            href="/login"
            class="text-bg-secondary hover:underline">Log in</a
        >
    </p>
</div>
