$(document).ready(function(){
    $("button#editbutton").click(function(){
      add_entry_to_db();
    });
});

function add_entry_to_db() {
      $.post("", {'title' : $("[name=title]").val(), 'text' : $("[name=text]").val()});
}