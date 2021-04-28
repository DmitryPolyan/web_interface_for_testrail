document.querySelectorAll('#list_of_projects').forEach(
  elem => {
    elem.onclick = () => {
      alert(document.getElementById('list_of_projects').value);
      $.get("/xtra", function(data, status){
        alert("Data: " + data + "\nStatus: " + status);
      });
    }
  }
);
