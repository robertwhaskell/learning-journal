Feature: Markdown entries
    Entries should display as markdown objects.

    Scenario: Entry is markdown
        Given an entry with title "Markdown Test"
        When I see the entry on the index page
        Then I see that it is a markdown entry