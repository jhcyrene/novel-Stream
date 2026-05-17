
document.addEventListener('DOMContentLoaded', function() {
    const profileToggle = document.getElementById('profileToggle');
    const profileMenu = document.getElementById('profileMenu');
    
    // 1. Toggle the menu when the profile icon is clicked
    if (profileToggle && profileMenu) {
        profileToggle.addEventListener('click', function(e) {
            e.preventDefault(); // Stop the link from navigating to #
            e.stopPropagation(); // Stop the click from immediately bubbling up to the document click handler
            profileMenu.classList.toggle('active');
        });
    }

    // 2. Close the menu when the user clicks anywhere else on the page
    document.addEventListener('click', function(e) {
        if (profileMenu && profileMenu.classList.contains('active') && !profileMenu.contains(e.target)) {
            profileMenu.classList.remove('active');
        }
    });
});