document.addEventListener("DOMContentLoaded", function () {
    console.log("Warehouse Management System Loaded!");

    // Auto-hide alert message after 3 seconds
    const alertBox = document.getElementById("alert-message");
    if (alertBox) {
        setTimeout(() => {
            alertBox.style.display = "none";
        }, 3000);
    }

    // Live inventory search (for future implementation)
    const searchBox = document.getElementById("search-product");
    if (searchBox) {
        searchBox.addEventListener("input", function () {
            const query = searchBox.value.toLowerCase();
            document.querySelectorAll(".product-row").forEach(row => {
                const productName = row.querySelector(".product-name").textContent.toLowerCase();
                row.style.display = productName.includes(query) ? "" : "none";
            });
        });
    }

    // Form validation for adding a product
    const addProductForm = document.getElementById("add-product-form");
    if (addProductForm) {
        addProductForm.addEventListener("submit", function (event) {
            const name = document.getElementById("product-name").value.trim();
            const quantity = document.getElementById("product-quantity").value;
            const price = document.getElementById("product-price").value;

            if (name === "" || quantity <= 0 || price <= 0) {
                event.preventDefault();
                alert("Please enter valid product details.");
            }
        });
    }
});
