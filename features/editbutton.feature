Feature: The detail page shouldn't have an edit button if you're not logged in.
    When you're not logged in, you can't see an edit button.

    Scenario: Select an entry
        Given a detail page
        When I'm not logged in
        Then I don't see an edit button
