function uploadFile(event) {
    // Prevent the default form submission behavior
    event.preventDefault();
  
    var fileInput = document.getElementById('receiptImage');
    var file = fileInput.files[0];
    if (!file) {
      alert('Please select a file');
      return;
    }
  
    var formData = new FormData();
    formData.append('file', file);
  
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.onload = function() {
      if (xhr.status === 200) {
        alert('File uploaded successfully');
      } else {
        alert('Error uploading file');
      }
    };
    xhr.send(formData);
  }
  