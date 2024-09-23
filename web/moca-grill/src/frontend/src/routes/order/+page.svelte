<script>
    import { onMount } from "svelte";
    import Spinner from "../../components/Spinner/Spinner.svelte";
    import DropdownReviewForm from "../../components/DropdownReviewForm/DropdownReviewForm.svelte";

    let orders = [];
    let token = null;
    let error = null;

    onMount(async () => {
        token = localStorage.getItem("token");
        if (!token) {
            document.location = "/login";
        }

        try {
            const response = await fetch("/api/v1/order/", {
                headers: {
                    Authorization: `Token ${token}`,
                },
            });
            if (response.ok) {
                orders = await response.json();
            } else {
                error = "Failed to fetch orders";
            }
        } catch (error) {
            error = "Failed to fetch orders";
        }
    });
</script>

<div class="flex min-h-screen w-3/4">
    <div class="w-3/4 p-8 bg-gray-100">
        <h1 class="text-3xl font-bold mb-8">Orders</h1>
        {#if orders.length > 0}
            <div class="grid grid-cols-1 gap-4">
                {#each orders as o}
                    <div class="bg-white shadow-lg rounded-lg p-6">
                        <div class="flex justify-between">
                            <h2 class="text-2xl font-semibold mb-2">
                                {o.shop_name}
                            </h2>
                            <h2 class="text-2xl font-semibold mb-2">
                                € {o.total}
                            </h2>
                        </div>
                        {#each o.items as item}
                            <li class="flex justify-between items-center mb-2">
                                <span>{item.name}</span>
                                <span>x{item.quantity}</span>
                            </li>
                        {/each}

                        <DropdownReviewForm order={o} token={token} />
                    </div>
                {/each}
            </div>
        {:else}
            <Spinner />
        {/if}
    </div>
</div>
