$(document).ready(function(){
    $("button#butid").click(function(){
      add_entry_to_db();
    });
});

function add_entry_to_db() {
      $.post("/add", {'title' : $("[name=title]").val(), 'text' : $("[name=text]").val()},
        append_entry, "json");
}

function append_entry(data){
      var id = data['id'];
      $('div#newentry').prepend("\
        <article class='entry' id='entry="+id+"'>\
        <h3>"+data['title']+"</h3>\
        <p>"+data['created']+"</p>\
        <div class='entry_body'>"+data['text']+"</div>\
        <a href='/details/"+id+"' id='"+id+"'><button>Detail View</button></a>\
        <article>\
        ");       
        
}