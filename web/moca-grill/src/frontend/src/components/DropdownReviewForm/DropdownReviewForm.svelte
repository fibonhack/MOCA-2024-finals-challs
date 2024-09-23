<script>
    import { onMount } from "svelte";

    export let order;
    export let token;

    let rating = 0;
    let comment = "";
    let show = false;

    const submitReview = async () => {
        try {
            let response = await fetch(`/api/v1/order/${order.id}/review/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify({
                    rating,
                    comment,
                }),
            });

            if (response.ok) {
                alert("Review submitted successfully");
            } else {
                alert("Failed to submit review");
            }
        } catch (error) {
            console.error(error);
        }

        show = false;
    }
</script>

<div
    class="flex items-center justify-between cursor-pointer mt-5"
    on:click={() => {
        show = !show;
    }}
>
    <h2 class="text-xl font-bold">Write a Review</h2>
    <svg
        class="w-6 h-6 transform {show
            ? 'rotate-180'
            : ''} transition-transform"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
    >
        <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 9l-7 7-7-7"
        ></path>
    </svg>
</div>

{#if show}
    <form on:submit|preventDefault={submitReview} class="mt-4">
        <!-- Star Rating Dropdown -->
        <div class="mb-4">
            <label for="rating" class="block text-gray-700 mb-2">Rating</label>
            <select
                id="rating"
                bind:value={rating}
                class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                <option value="0">0 Stars</option>
                <option value="1">1 Star</option>
                <option value="2">2 Stars</option>
                <option value="3">3 Stars</option>
                <option value="4">4 Stars</option>
                <option value="5">5 Stars</option>
            </select>
        </div>

        <div class="mb-6">
            <label for="comment" class="block text-gray-700 mb-2">Comment</label
            >
            <textarea
                id="comment"
                bind:value={comment}
                rows="4"
                class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Write your review here..."
            ></textarea>
        </div>

        <button
            type="submit"
            class="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-secondary"
        >
            Submit Review
        </button>
    </form>
{/if}
