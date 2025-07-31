// JavaScript for any interactive functionality
document.addEventListener('DOMContentLoaded', function() {
    // Hide/show navbar on scroll
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');
    
    // Ensure navbar exists before adding scroll listener
    if (navbar) {
        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll <= 0) {
                navbar.classList.remove('hidden');
                return;
            }
            
            if (currentScroll > lastScroll && !navbar.classList.contains('hidden')) {
                // Scroll down
                navbar.classList.add('hidden');
            } else if (currentScroll < lastScroll && navbar.classList.contains('hidden')) {
                // Scroll up
                navbar.classList.remove('hidden');
            }
            
            lastScroll = currentScroll;
        });
    }

    // Back to top button functionality
    const backToTopButton = document.getElementById('Totop');

    if (backToTopButton) {
        // Show or hide the button based on scroll position
        window.addEventListener('scroll', function() {
            if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                backToTopButton.style.display = "block"; // Show the button
            } else {
                backToTopButton.style.display = "none";  // Hide the button
            }
        });

        // Scroll to the top when the button is clicked
        backToTopButton.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth' // Smooth scrolling effect
            });
        });
    }

    // Burger menu creation and functionality
    const burgerMenu = document.createElement('button');
    burgerMenu.classList.add('burger-menu');
    burgerMenu.innerHTML = '<div></div><div></div><div></div>';
    
    const navList = document.querySelector('.navbar .list');
    const navSide = document.querySelector('.navbar .side');
    const logo = document.querySelector('.navbar .logo');

    // Insert burger menu right after the logo, if logo exists
    if (logo) {
        logo.insertAdjacentElement('afterend', burgerMenu);
    }

    burgerMenu.addEventListener('click', function () {
        if (navList) navList.classList.toggle('active');
        if (navSide) navSide.classList.toggle('active');
        burgerMenu.classList.toggle('open');

        // Adjust navbar alignment based on menu state
        if (navbar) {
            if (navList && navList.classList.contains('active')) {
                navbar.style.alignItems = 'flex-start'; // Align items to top when menu is open
            } else {
                navbar.style.alignItems = 'center'; // Reset to center when menu is closed
            }
        }
    });

    // Close menu if a link is clicked
    const navLinks = document.querySelectorAll('.list ul a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Check if the link is a dropdown item. If it is, the dropdown logic will handle closing.
            // If not, close the main menu.
            if (navList && navSide && burgerMenu && navbar && !link.closest('.dropdown-content')) {
                navList.classList.remove('active');
                navSide.classList.remove('active');
                burgerMenu.classList.remove('open');
                navbar.style.alignItems = 'center'; // Reset alignment
            }
        });
    });

    // Dropdown functionality for desktop and mobile
    const dropBtn = document.getElementById('dropBtn');
    const dropdownContent = document.querySelector('.dropdown-content');

    if (dropBtn && dropdownContent) {
        dropBtn.addEventListener('click', function(event) {
            event.stopPropagation(); // Prevent document click from closing immediately
            // Toggle the display for the dropdown content
            dropdownContent.style.display = dropdownContent.style.display === 'flex' ? 'none' : 'flex';

            // If the main menu is also open, ensure the navbar adjusts height if needed
            if (navbar && navList && navList.classList.contains('active')) {
                navbar.style.height = 'auto'; // Re-calculate height if menu is open and dropdown changes
            }
        });

        // Close dropdown if clicked outside
        document.addEventListener('click', function(event) {
            if (!dropBtn.contains(event.target) && !dropdownContent.contains(event.target)) {
                dropdownContent.style.display = 'none';
            }
        });
    }

    // Contact form functionality
    const contactButton = document.getElementById('Contact');
    const contactPage = document.querySelector('.Contact');
    const closeButton = document.getElementById('closeBtn');
    const footerContactLink = document.getElementById('contactPage');

    const closeContactForm = () => {
        if (contactPage) contactPage.style.display = 'none';
        // Ensure burger menu and dropdown are reset when contact form closes
        if (navList) navList.classList.remove('active');
        if (navSide) navSide.classList.remove('active');
        burgerMenu.classList.remove('open');
        if (navbar) navbar.style.alignItems = 'center';
        if (dropdownContent) dropdownContent.style.display = 'none';
    };

    if (contactButton) {
        contactButton.addEventListener('click', function(event) {
            event.preventDefault();
            if (contactPage) contactPage.style.display = 'flex';
            // Close the burger menu and dropdown when contact form is opened
            if (navList) navList.classList.remove('active');
            if (navSide) navSide.classList.remove('active');
            burgerMenu.classList.remove('open');
            if (navbar) navbar.style.alignItems = 'center';
            if (dropdownContent) dropdownContent.style.display = 'none';
        });
    }

    if (footerContactLink) {
        footerContactLink.addEventListener('click', function(event) {
            event.preventDefault();
            if (contactPage) contactPage.style.display = 'flex';
            // Close the burger menu and dropdown when contact form is opened
            if (navList) navList.classList.remove('active');
            if (navSide) navSide.classList.remove('active');
            burgerMenu.classList.remove('open');
            if (navbar) navbar.style.alignItems = 'center';
            if (dropdownContent) dropdownContent.style.display = 'none';
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', closeContactForm);
    }
});