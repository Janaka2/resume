
function copyText(id){
var text = document.getElementById(id).innerText;
navigator.clipboard.writeText(text);
alert("Prompt copied");
}
