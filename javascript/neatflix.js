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

function LoadAbout()
{
   $("#result_box").empty();
   $("#picture_box").html('');
   $("#info_box").html('');

   var pic = '<a class="about_link" href="http://www.netflix.com"><img src="http://android.appstorm.net/wp-content/uploads/2011/05/icon.gif" width="110px"/></a>'

   var msg = 'Neatflix is a way to quickly search the <a class="about_link" href="http://www.netflix.com">Netflix</a> ' +
             'database to find more information about movies and tv shows. The API calls were originally written in ' +
             'javascript, but later moved to the server (python) due to the realization that the oAuth secret key was ' +
             'shared in viewable source. Not a good practice.<br><br>' +
             'This demo was built by <a class="about_link" href="http://www.alexanderle.com">Alex Le</a> to learn ' +
             'more about the <a class="about_link" href="http://developer.netflix.com/page">Netflix API</a>.'

   $("#picture_box").append(pic)
   $("#info_box").append(msg);
}

$(document).ready(function () {
   $("#search_box").keyup(function (event) {
      if (event.keyCode == 13) {
         GetNetflixAuto();
      }
   });
});

