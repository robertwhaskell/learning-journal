Feature: You can see an edit button when you're logged in
    If you're logged in, you can see the edit button.

    Scenario: Select an entry
        Given a login page
        When I log in and go to an editing page
        Then I see the edit button
