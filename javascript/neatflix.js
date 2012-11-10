$(function() {
   $("#search_box").focus();
});

$(document).ready(function () {
   $("#search_box").keyup(function (event) {
      if (event.keyCode == 13) {
         GetNetflixAuto();
      }
   });
});

