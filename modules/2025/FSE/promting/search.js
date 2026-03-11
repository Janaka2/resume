
function searchContent(){
var input = document.getElementById("searchBox").value.toLowerCase();
var links = document.querySelectorAll(".sidebar ul li");

links.forEach(function(li){
var text = li.innerText.toLowerCase();
li.style.display = text.includes(input) ? "" : "none";
});
}
