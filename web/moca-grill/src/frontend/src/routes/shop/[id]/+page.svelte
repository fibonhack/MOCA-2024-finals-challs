<script>
    import { onMount } from "svelte";
    import Spinner from "../../../components/Spinner/Spinner.svelte";
    import LateralMenu from "../../../components/LateralMenu/LateralMenu.svelte";

    export let data;

    let shop = null;
    let menu = [];
    let token = null;
    let error_msg = null;
    let reviews = [];

    onMount(async () => {
        token = localStorage.getItem("token");

        try {
            const response = await fetch(`/api/v1/shop/${data.shop_id}/`);
            if (response.ok) {
                shop = await response.json();
            } else {
                error_msg = "Shop does not exists";
                return;
            }
        } catch (err) {
            error_msg = "Shop does not exists";
            return;
        }

        try {
            const response = await fetch(`/api/v1/shop/${shop.id}/menu/`);
            if (response.ok) {
                menu = await response.json();
            } else {
                error_msg = "Failed to fetch menu";
            }
        } catch (err) {
            error_msg = "Failed to fetch menu";
        }

        try {
            const response = await fetch(`/api/v1/shop/${shop.id}/review/`);
            if (response.ok) {
                reviews = await response.json();
            } else {
                error_msg = "Failed to fetch reviews";
            }
        } catch (err) {
            error_msg = "Failed to fetch reviews";
        }
    });

    const addItem = async (item) => {
        let cart = localStorage.getItem("cart");
        if (!cart) {
            cart = [];
        } else {
            cart = JSON.parse(cart);
        }

        let done = false;
        for (let c of cart) {
            if (c.id == item.id) {
                c.quantity++;
                done = true;
                break;
            }
        }

        if (!done) {
            cart.push({
                id: item.id,
                name: item.name,
                price: item.price,
                quantity: 1,
            });
        }

        localStorage.setItem("cart", JSON.stringify(cart));
    };
</script>

<div class="flex min-h-screen w-3/4">
    <div class="w-3/4 p-8 bg-gray-100">
        <h1 class="text-3xl font-bold mb-8">Menu</h1>
        {#if menu.length > 0}
            <div class="grid grid-cols-1 gap-4">
                {#each menu as item}
                    <div
                        class="bg-white shadow-lg rounded-lg p-6 flex justify-between"
                    >
                        <div class="">
                            <h2 class="text-2xl font-semibold mb-2">
                                {item.name} - € {item.price}
                            </h2>
                            <p class="text-gray-700 mb-4">{item.description}</p>
                        </div>

                        <div class="flex justify-center">
                            <button
                                on:click={() => {
                                    addItem(item);
                                }}
                            >
                                <img
                                    src="/plus.svg"
                                    alt=""
                                    width="20px"
                                    height="20px"
                                />
                            </button>
                        </div>
                    </div>
                {/each}
            </div>

            <hr class="h-px my-8 bg-gray-200 border-0 dark:bg-gray-700" />

            {#if reviews.length > 0}
                <div class="grid grid-cols-1 gap-4">
                    {#each reviews as r}
                        <div class="bg-white shadow-lg rounded-lg p-6">
                            <h2 class="text-2xl font-semibold mb-2">
                                {r.user} says:
                            </h2>
                            <h4 class="text-lg font-semibold mb-2">
                                Rating: {r.rating} star(s)
                            </h4>
                            <p class="text-gray-700 mb-4">{r.comment}</p>
                        </div>
                    {/each}
                </div>
            {:else}
                <div class="bg-white shadow-lg rounded-lg p-6">
                    <p class="text-gray-700 mb-4">No reviews yet</p>
                </div>
            {/if}
        {:else if error_msg}
            <p class="text-red-500">{error_msg}</p>
        {:else}
            <Spinner />
        {/if}
    </div>

    <LateralMenu bind:shop={shop} />
</div>
