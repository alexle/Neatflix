$(function() {
   $("#search_box").focus();
});

function GetNetflixAuto()
{
   $("#result_box").empty();
   $("#picture_box").html('');
   $("#info_box").html('');

   var url = "http://api.netflix.com/catalog/titles/autocomplete";
   var search_string = $("#search_box").val();
   var key = "adqe4ngafwj8ybwvnfgbnuta";

   $.get(
      url,
      { term: search_string, oauth_consumer_key: key },
      function(data) {
         $(data).find('title').each(function(index) {
            result_title = $(this).attr('short');

            $("#result_box").append(
               '<form method="post"><input type="hidden" name="user" value="' +
               result_title + '" /><input id="search_button" type="submit" value="' +
               result_title + '"/></form>')
         });
      }
   );
}

$(document).ready(function () {
   $("#search_box").keyup(function (event) {
      if (event.keyCode == 13) {
         GetNetflixAuto();
      }
   });
});

