function showRoleFields() {

    const role = document.getElementById("role");

    const studentFields =
        document.getElementById("studentFields");

    const facultyFields =
        document.getElementById("facultyFields");


    if (!role) {
        return;
    }


    studentFields.style.display = "none";
    facultyFields.style.display = "none";


    if (role.value === "student") {

        studentFields.style.display = "block";

    }


    if (role.value === "faculty") {

        facultyFields.style.display = "block";

    }

}


// Confirm cancel/delete actions

document.addEventListener("DOMContentLoaded", function () {

    const confirmButtons =
        document.querySelectorAll("[data-confirm]");


    confirmButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            const message =
                button.getAttribute("data-confirm");

            if (!confirm(message)) {

                event.preventDefault();

            }

        });

    });

});