Feature: Edit Features


    Scenario Outline: checking to see if things are edited correctly
        Go to the home page
        Click the detail button of an entry
        Then I see the entries text and title on the detail page
        Click the edit button on the detail page
        Edit the entry
        Then I see the change on the home page

    Scenario Outline: I should be able to delete entries entirely
        Go to an entry's edit page
        Press the delete button
        Then I see that the entry is gone from the homepage
        Then I see that the entry is gone from the database