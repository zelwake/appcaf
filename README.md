# AppCAF
#### Video Demo: <https://youtu.be/-VBuk652J6E>
#### Description:

This application should help you with learning new words in different languages.
There is an internal database of words that users can expand. To access the application, user have to register with name and password. No need for email or other things.

Inside the application, user can create new word pairs for languages Czech, English and French or create test for practicing language of choice.
On dashboard user can see all of their unfinished test while on test page, they see all of their tests.

#### Technology used:

- Flask
- Werkzeug.security
  - generating and checking password hash
- SQLite
- CS50 for SQL connection
  - I wanted to practice SQL statements instead of relying on ORM. Sadly I cannot deploy the application due to using this library
- HTMX javascript library
  - Small library that adds some great functionality to all HTML elements, practically turning the web application into SPA-like app
- Bootstrap for CSS
  - I am a bit lazy and this helped me create okay-ish looking application, right now only for mobile

#### Database:

Database schema can be found inside `database.sql` file in root directory. Database itself has 3 similar tables for storing words, each for single language. Then 3 more similar tables for pairing these words between themselves. Test table that hold information about test itself (languages used, current and total rounds, start and finish time), test_word_relation table that stores information about each word per test id and round of said test. Finally, account and test_account_relation to keep track of users tests. 

#### Source directory:

In root of the project, there is only db.py and languages.py files that are used by the app. Since the app was not going to be small, I decided to split main.py into multiple blueprints as suggested by flask documentation.
All the blueprints are loaded inside `/app/__init__.py` file as well as application settings for database and session.

In root of the project there is also directory called helpers which contains some helper functions that were used across the application. `Check_password.py` to check if password fit all requirements.
`Database_helpers.py` contain some functions to check which database pair table should I call, insertion of word pairs, transform of dictionary to list and two enums.
Then there is `login_required` wrapper for pages inside application restricted for logged users. Lastly there are two files for htmx specifics. One to check if HTTP request contains HTMX header and second one to create HTTP response with HTMX template.

Moving into app directory, there are directories `static`, `blueprints` and `templates`. Static contains minified HTMX library, custom css file and public directory with images. File `styles.css` is mainly used inside `test_results.html` template for pie chart and subgrid table. 
Blueprints have files for many of the routes, each with similar theme explained below.

#### `root.py`
This file is rendering main page as `/` route.

#### `auth.py`
This file is handling login, logout and register with `render_register_page` helper function.
- `/logout` route only clears session and redirect user to `/` route.
- `/login` route renders on `GET` request form. On `POST` request it clears session, then check is username and password are provided, then check database if said user exists and finally `check_password_hash` of provided password. If all is valid, it will redirect user to `/app` route, where they gain access to all the application functionalities.
- `/register` route is handling registering of new users. For `POST` request it firstly checks if username, password and repeated password are provided. Then checks if password and repeated password are same. Afterward run `check_password` function if password is valid. Only after all that a sql query is queued to check whether username is already in use (both usernames are transformed to lowercase). If no such user exists we can create one with hashed password and store it in database and redirect user to `/login` page. `GET` only renders registration form with error messages if any occur.

#### `app.py`
This files handles `/app` route dashboard. It's getting user's name from database for greeting message and loading last five unfinished tests inside html table.

#### `test.py` 
As this file is quite a big one, so I decided to split routes using `test_bp.get` and `test_bp.post` methods to keep the code more readable.
- `/app/test` has only `GET` method and shows all the test user has created, finished or not
- `/app/test/new` 
  - `GET` method only renders form for creating a new test, loading possible test languages from file `languages.py`
  - `POST` method checks if languages were provided, are not same and do actually exist. Then check if number of words is provided and is a positive integer. Final check is if word pair table for these two languages exists. If all these checks are passed, query for randomly selecting words from database is queued with limit to number of words from form. `number_of_words` is afterward changed to number of pairs that were returned by database, because there may not be enough of the words yet. Few more queries are created inside `BEGIN TRANSACTION` and `COMMIT` to prevent race conditions:
      - new test is created with number of words and languages
      - since CS50 sql adapter is not returning id of newly inserted row, I have to run `SELECT` to find the id of test this way
      - for each pair of word_pairs a new query insertion is created
      - finally, test_account_relation is stored in database, so user can access this test
      - if at any point `db.execute` throws an exception, whole transaction will be `ROLLBACK` and error message will be shown to user
        
    Then user will be redirected to `/app/test/<id>`.
- `/app/test/<id>`
  - `GET` method is rendering test form. It checks database to see, if said test is tied to this user, it's not finished yet, skip is used in url query (for skipping answer), load new word to translate from database, and if two tries were used it also loads answer or answers to show to user. If any of these checks fails, user is instead redirected to `/app/test` or `/app/test/<id>/results` as the test is either not their, its finished or test is somehow broken in other way and not finish-able.
  - `POST` method is again checking if test_id belongs to the user and if answer is provided. Then loads possible answers from database, turn them into list, load which try of user it is, checks if answer is one of the possible answers. Then it will set the answer to `test_word_relation` table together with number of tries, if answer was right also update round or if it was last round, also set test to finished. Then it renders if user was right or wrong, possible answers after second try and buttons to move user to next part.
- `/app/test/<id>/results` has only `GET` method. It will again check is said test_id belongs to user and test is finished. Afterward it query 4 tables together with JOINS to return all the information about test together with all possible answers, all user answers, languages and statistics.

#### `word.py` 
  - `/app/word` route is handling creation of new words and rendering form to add them.
    - `GET` method is only rendering form and use pass query parameters to url is any were present
    - `POST` method is checking if at least 2 word were provided. Set word ids to zero (AKA doesn't exist inside database yet), then looks for the id of words with `get_word_id` helper function. This function looks into database to see if word exists. If yes, it's going to return its id, otherwise it will insert it and return its new id. After this it's going to create pairs for each word provided and return message if everything worked or not.

`Templates` directory contains `layout.html`, which is shared across the whole application and has all the files from static loaded into.
Rest of the templates are there to extends layout and include partials inside `partials` directory with same name.
Files inside `partials` directory are used as htmx render return, while files inside `templates` are used when non HTMX HTTP request happened.
This helps serve user the right file based on if HTMX request was issued or not.

