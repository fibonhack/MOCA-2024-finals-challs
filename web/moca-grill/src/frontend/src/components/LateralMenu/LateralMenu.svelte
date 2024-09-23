<script>
    import { onMount } from "svelte";

    let token = null;
    let cart = null;
    let total = 0;

    export let shop;

    onMount(async () => {
        token = localStorage.getItem("token");
        cart = localStorage.getItem("cart");
        if (cart) {
            cart = JSON.parse(cart);
            total = cart
                .map((x) => {
                    return x.price * x.quantity;
                })
                .reduce((a, b) => {
                    return a + b;
                }, 0);
        }
    });

    const handleBuy = async () => {
        if (!cart) {
            return;
        }

        let order = {
            items: cart.map((item) => {
                return {
                    item: item.id,
                    quantity: item.quantity,
                };
            }),
        };

        try {
            let response = fetch(`/api/v1/shop/${shop.id}/order/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify(order),
            });

            localStorage.removeItem("cart");
            cart = null;
            total = 0;

            if (response.ok) {
                document.location = "/orders";
            } else {
                document.location = "/";
            }
        } catch (err) {
            document.location = "/";
        }
    };
</script>

<div class="w-1/4 bg-secondary text-white p-4">
    {#if !token}
        <p>Login to add to the cart</p>
        <button
            class="mt-4 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
            on:click={() => {
                document.location = "/login/";
            }}
        >
            Login
        </button>
    {:else}
        <h2 class="text-xl font-bold mb-4">Cart</h2>
        {#if cart}
            <ul>
                {#each cart as item}
                    <li class="flex justify-between items-center mb-2">
                        <span>{item.name}</span>
                        <span>x{item.quantity}</span>
                    </li>
                {/each}
                <li class="flex justify-between items-center mb-2">
                    <span><b>Total</b></span>
                    <span>€ {total.toFixed(2)}</span>
                </li>
            </ul>
            <button
                type="submit"
                class="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary"
                on:click|preventDefault={handleBuy}>CHECKOUT</button
            >
        {:else}
            <p>Your cart is empty</p>
        {/if}
    {/if}
</div>
