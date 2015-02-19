$(document).ready(function(){
    $("button#butid").click(function(){
      $.post("/add", {'title' : $("[name=title]").val(), 'text' : $("[name=text]").val()},
        function(data){
          var id = data['id']
          $('div#newentry').prepend("\
            <article class='entry' id='entry="+id+"'>\
            <h3>"+data['title']+"</h3>\
            <p>dateline</p>\
            <div class='entry_body'>"+data['text']+"</div>\
            <a href='/details/"+id+"' id='"+id+"'><button>Detail View</button></a>\
            <article>\
            ")          
        }, "json");
    });
});