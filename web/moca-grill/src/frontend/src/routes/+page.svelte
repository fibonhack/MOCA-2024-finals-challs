<script>
    import { onMount } from "svelte";
    import Spinner from "../components/Spinner/Spinner.svelte";

    let shops = [];
    let token = null;
    let error = null;

    onMount(async () => {
        token = localStorage.getItem("token");
        try {
            const response = await fetch("/api/v1/shop/");
            if (response.ok) {
                shops = await response.json();
            } else {
                error = "Failed to fetch shops";
            }
        } catch (error) {
            error = "Failed to fetch shops";
        }
    });
</script>

<div class="flex min-h-screen w-3/4">
    <div class="w-3/4 p-8 bg-gray-100">
        <h1 class="text-3xl font-bold mb-8">Shops</h1>
        {#if shops.length > 0}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {#each shops as shop}
                    <div class="bg-white shadow-lg rounded-lg p-6">
                        <a href="/shop/{shop.id}/">
                            <h2 class="text-2xl font-semibold mb-2">
                                {shop.name}
                            </h2>
                        </a>
                        <p class="text-gray-700 mb-4">{shop.description}</p>
                        <span class="text-sm text-gray-500"
                            >Since: {new Date(
                                shop.created_at,
                            ).toLocaleDateString()}</span
                        >
                    </div>
                {/each}
            </div>
        {:else}
            <Spinner />
        {/if}
    </div>
</div>
