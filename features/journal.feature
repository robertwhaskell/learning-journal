Feature: Journal Detail Page
    Select an entry from the learning journal and check it's detail page

    Scenario: Select an entry
        Given an entry with the title "test title"
        When I press the detail button
        Then I see the detail page for that entry
