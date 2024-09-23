<script>
    import { onMount } from "svelte";
    import { VERSION } from "../constants";

    const TOKEN = "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";

    // Check if admin
    const username = "mocarrosticino";
    const repoName = "moca-grill";
    let token = null;
    let user = null;
    let last_version = null;

    onMount(async () => {
        token = localStorage.getItem("token");

        if (!token) {
            document.location.href = "/login/";
        }

        try {
            const response = await fetch("/accounts/profile/", {
                headers: {
                    Authorization: `Token ${token}`,
                },
            });

            if (!response.ok) {
                document.location.href = "/login/";
            }

            user = await response.json();
        } catch (error) {
            document.location.href = "/login/";
        }

        if (!user || !user.is_superuser) {
            document.location.href = "/";
        }

        try {
            const response = await fetch(
                `https://api.github.com/repos/${username}/${repoName}/releases`,
                {
                    method: "GET",
                    headers: {
                        Authorization: `token ${TOKEN}`,
                        Accept: "application/vnd.github+json",
                    },
                },
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            console.log(VERSION);

            if (data.length > 0) {
                const last_element = data[0];
                const tag_name = last_element.tag_name;
                last_version = tag_name.replace("v", "");
            }
        } catch (error) {
            console.error("Error fetching releases:", error);
        }
    });
</script>

{#if last_version != VERSION}
    <div>
        <h1>Update available</h1>
        <p>
            A new version of the website is available. Please update to the
            latest version.
        </p>
        <p>
            Current version: {VERSION}
        </p>
        <p>
            Latest version: {last_version}
        </p>

        <a href="https://github.com/repos/${username}/${repoName}/releases">
            UPDATE</a
        >
    </div>
{:else}
    <div>
        <h1>No updates available</h1>
        <p>You are using the latest version of the website.</p>
    </div>
{/if}
