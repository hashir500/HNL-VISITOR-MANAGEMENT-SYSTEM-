document.addEventListener("DOMContentLoaded", function () {
    const accountType = document.getElementById("id_account_type");
    const password1Row = document.querySelector(".form-row.field-password1");
    const password2Row = document.querySelector(".form-row.field-password2");

    function togglePasswordFields() {
        if (!accountType) return;

        if (accountType.value === "m365") {
            if (password1Row) password1Row.style.display = "none";
            if (password2Row) password2Row.style.display = "none";

            const password1 = document.getElementById("id_password1");
            const password2 = document.getElementById("id_password2");

            if (password1) password1.required = false;
            if (password2) password2.required = false;
        } else {
            if (password1Row) password1Row.style.display = "";
            if (password2Row) password2Row.style.display = "";

            const password1 = document.getElementById("id_password1");
            const password2 = document.getElementById("id_password2");

            if (password1) password1.required = true;
            if (password2) password2.required = true;
        }
    }

    if (accountType) {
        accountType.addEventListener("change", togglePasswordFields);
        togglePasswordFields();
    }
});