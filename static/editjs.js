$(document).ready(function(){
    $("button#tweetbutton").click(function(){
        tweet_entry();
    });
    $("button#editbutton").click(function(){
      add_entry_to_db();
    });
});

function add_entry_to_db() {
    $.post("", {'title' : $("[name=title]").val(), 'text' : $("[name=text]").val()});
}

function tweet_entry(){
    $.get("/tweet", {'title' : $("[name=title]").val()});
}