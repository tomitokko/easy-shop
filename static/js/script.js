// Get the DOM element with id "navbar" and assign it to the variable "navbar"
const navbar = document.getElementById("navbar");

// Get the first DOM element with class "menu-btn" and assign it to the variable "menuBtn"
const menuBtn = document.querySelector(".menu-btn");

// Initialize a boolean variable "menuOpen" to false
let menuOpen = false;

// Add a "click" event listener to the "menuBtn" element, and execute the following function when it is clicked
menuBtn.addEventListener("click", () => {
  // If the "menuOpen" variable is currently false
  if (!menuOpen) {
  // Add the class "open" to the "menuBtn" element
  menuBtn.classList.add("open");
  // Add the class "open" to the "navbar" element
  navbar.classList.add("open");
  // Update the "menuOpen" variable to true
  menuOpen = true;
  }
  // If the "menuOpen" variable is currently true
  else {
  // Remove the class "open" from the "menuBtn" element
  menuBtn.classList.remove("open");
  // Remove the class "open" from the "navbar" element
  navbar.classList.remove("open");
  // Update the "menuOpen" variable to false
  menuOpen = false;
  }
});