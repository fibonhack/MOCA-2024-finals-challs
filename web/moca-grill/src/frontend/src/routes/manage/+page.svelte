<script>
    import { onMount } from "svelte";
    import Spinner from "../../components/Spinner/Spinner.svelte";

    let user = null;
    let reviews = [];
    let token = null;
    let error = null;

    onMount(async () => {
        token = localStorage.getItem("token");

        if (!token) {
            document.location.href = "/login/";
        }

        try {
            const response = await fetch("/accounts/profile", {
                headers: {
                    Authorization: `Token ${token}`,
                },
            });

            if (response.ok) {
                user = await response.json();
            } else {
                document.location.href = "/login/";
            }
        } catch (error) {
            document.location.href = "/login/";
        }

        if (!user || !user.is_staff) {
            document.location.href = "/";
        }

        try {
            const response = await fetch("/api/v1/manage/", {
                headers: {
                    Authorization: `Token ${token}`,
                },
            });

            if (response.ok) {
                reviews = await response.json();
            } else {
                error = "Failed to fetch reviews";
            }
        } catch (error) {
            error = "Failed to fetch reviews";
        }
    });

    const approve = async (review) => {
        try {
            const response = await fetch(`/api/v1/manage/${review.id}/`, {
                method: "PATCH",
                headers: {
                    Authorization: `Token ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    approved: true,
                }),
            });

            if (response.ok) {
                document.location.reload();
            } else {
                error = "Failed to approve review";
            }
        } catch (err) {
            error = "Failed to approve review";
        }
    };
</script>

<div class="flex min-h-screen w-3/4">
    <div class="w-3/4 p-8 bg-gray-100">
        <h1 class="text-3xl font-bold mb-8">Reviews</h1>
        {#if reviews.length > 0}
            <div class="grid grid-cols-1 gap-4">
                {#each reviews as r}
                    <div class="bg-white shadow-lg rounded-lg p-6">
                        <a href="/shop/{r.id}/">
                            <h2 class="text-2xl font-semibold mb-2">
                                From: {r.user}
                            </h2>

                            <h4 class="text-lg font-semibold mb-2">
                                Rating: {r.rating} star(s)
                            </h4>
                        </a>
                        <p class="text-gray-700 mb-4">{r.comment}</p>
                        <div class="flex justify-between">
                            <span class="text-sm text-gray-500"
                                >Posted on: {new Date(
                                    r.created_at,
                                ).toLocaleDateString()}</span
                            >
                            {#if r.approved}
                                <span class="text-sm text-green-500"
                                    >Approved</span
                                >
                            {:else}
                                <button
                                    class="mt-4 bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary"
                                    on:click={() => {
                                        approve(r);
                                    }}
                                >
                                    Approve
                                </button>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        {:else}
            <Spinner />
        {/if}
    </div>
</div>
