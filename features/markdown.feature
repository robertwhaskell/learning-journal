Feature: Markdown/Colorization Features


    Scenario Outline: Entries should display on the home page as markdown objects.
        When I see an entry on the "<pagename>" page with the text "<text>"
        Then I see that it "<is_or_isnt>" a markdown entry

    Examples:
        | pagename   | text     | is_or_isnt
        | /          | Test Text | is
