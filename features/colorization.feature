Feature: markup text is colorized
    Select an entry from the learning journal and check if it's colorized

    Scenario: Select an entry
        Given an entry with the title "Color Testing"
        When I see the entry on the index page
        Then I see the entry is colorized
