Feature: Markdown/Colorization Features


    Scenario Outline: Entries should display on the home page as markdown objects.
        When I see an entry on the "<pagename>" page with the title "<title>"
        Then I see that it is a markdown entry

    Examples:
        | pagename   | title      |
        | /          | Test Title |
        | /details/1 | Test Title |
